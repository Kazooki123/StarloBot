mod error;

use std::process::{Command, Child};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use std::thread;
use std::fs;
use tokio::signal;
use serde::{Deserialize, Serialize};
use warp::{Filter, Reply};
use tokio::runtime::Runtime;
use log::error;
use error::{BotError, AuthError, ApiError};

#[derive(Debug, Deserialize)]
struct Config {
    server: ServerConfig,
    bot: BotConfig,
    sharding: ShardingConfig,
    monitoring: MonitoringConfig,
}

#[derive(Debug, Deserialize)]
struct ServerConfig {
    host: String,
    port: u16,
    token: String,
}

#[derive(Debug, Deserialize)]
struct BotConfig {
    python_path: String,
    script_path: String,
}

#[derive(Debug, Deserialize)]
struct ShardingConfig {
    total_shards: usize,
    node_id: usize,
    shards: Vec<usize>,
}

#[derive(Debug, Deserialize)]
struct MonitoringConfig {
    check_interval_seconds: u64,
    restart_cooldown_seconds: u64,
    max_restart_attempts: usize,
}

#[derive(Serialize)]
struct ShardStatus {
    id: usize,
    running: bool,
    restart_count: usize,
    last_restart: String,
}

#[derive(Serialize)]
struct NodeStatus {
    node_id: usize,
    shards: Vec<ShardStatus>,
}

struct BotShard {
    id: usize,
    process: Option<Child>,
    last_restart: Instant,
    restart_count: usize,
    max_restart_attempts: usize,
}

impl BotShard {
    fn new(id: usize, max_restart_attempts: usize) -> Self {
        BotShard {
            id,
            process: None,
            last_restart: Instant::now(),
            restart_count: 0,
            max_restart_attempts,
        }
    }

    fn start(&mut self, python_path: &str, script_path: &str, shard_id: usize, shard_count: usize) -> Result<(), String> {
        if let Some(mut process) = self.process.take() {
            let _ = process.wait();
        }

        let process = Command::new(python_path)
            .arg(script_path)
            .env("SHARD_ID", shard_id.to_string())
            .env("SHARD_COUNT", shard_count.to_string())
            .spawn()
            .map_err(|e| format!("Failed to start bot shard {}: {}", self.id, e))?;

        self.process = Some(process);
        self.last_restart = Instant::now();
        self.restart_count += 1;

        println!("Started bot shard {} (restart #{})", self.id, self.restart_count);
        Ok(())
    }

    fn is_running(&mut self) -> bool {
        if let Some(process) = &mut self.process {
            match process.try_wait() {
                Ok(None) => true,
                _ => false,
            }
        } else {
            false
        }
    }

    fn stop(&mut self) -> Result<(), String> {
        if let Some(mut process) = self.process.take() {
            process.kill().map_err(|e| format!("Failed to kill bot shard {}: {}", self.id, e))?;
        }
        Ok(())
    }

    fn status(&mut self) -> ShardStatus {
        ShardStatus {
            id: self.id,
            running: self.is_running(),
            restart_count: self.restart_count,
            last_restart: format!("{:?} ago", self.last_restart.elapsed()),
        }
    }
}

struct NodeManager {
    node_id: usize,
    shards: HashMap<usize, BotShard>,
    python_path: String,
    script_path: String,
    total_shards: usize,
    restart_cooldown: Duration,
    max_restart_attempts: usize,
}

impl NodeManager {
    fn new(config: &Config) -> Self {
        NodeManager {
            node_id: config.sharding.node_id,
            shards: HashMap::new(),
            python_path: config.bot.python_path.clone(),
            script_path: config.bot.script_path.clone(),
            total_shards: config.sharding.total_shards,
            restart_cooldown: Duration::from_secs(config.monitoring.restart_cooldown_seconds),
            max_restart_attempts: config.monitoring.max_restart_attempts,
        }
    }

    fn add_shard(&mut self, shard_id: usize) -> Result<(), String> {
        if shard_id >= self.total_shards {
            return Err(format!("Shard ID {} exceeds total shards {}", shard_id, self.total_shards));
        }

        if self.shards.contains_key(&shard_id) {
            return Err(format!("Shard {} already exists on this node!", shard_id));
        }

        let mut shard = BotShard::new(shard_id, self.max_restart_attempts);
        shard.start(&self.python_path, &self.script_path, shard_id, self.total_shards)?;
        self.shards.insert(shard_id, shard);

        Ok(())
    }

    fn monitor_shards(&mut self) {
        for (shard_id, shard) in self.shards.iter_mut() {
            if !shard.is_running() && shard.last_restart.elapsed() > self.restart_cooldown {
                println!("Shard {} is not running. Attempting restart...", shard_id);

                if shard.restart_count >= self.max_restart_attempts {
                    eprintln!("WARNING: Shard {} has exceeded max restart attempts ({})", shard_id, self.max_restart_attempts);
                }

                if let Err(e) = shard.start(&self.python_path, &self.script_path, *shard_id, self.total_shards) {
                    eprintln!("Failed to restart shard {}: {}", shard_id, e);
                }
            }
        }
    }

    fn stop_all(&mut self) {
        for (id, shard) in self.shards.iter_mut() {
            if let Err(e) = shard.stop() {
                eprintln!("Error stopping shard {}: {}", id, e);
            }
        }
    }

    fn status(&mut self) -> NodeStatus {
        let shard_statuses = self.shards.iter_mut()
            .map(|(_, shard)| shard.status())
            .collect();

        NodeStatus {
            node_id: self.node_id,
            shards: shard_statuses,
        }
    }

    fn restart_shard(&mut self, shard_id: usize) -> Result<(), String> {
        let shard = self.shards.get_mut(&shard_id)
            .ok_or_else(|| format!("Shard {} not found on this node!", shard_id))?; 

        shard.start(&self.python_path, &self.script_path, shard_id, self.total_shards)
    }
}

impl Config {
    fn validate(&self) -> Result<(), String> {
        if self.sharding.total_shards == 0 {
            return Err("total_shards must be greater than 0".to_string());
        }
        if self.monitoring.check_interval_seconds == 0 {
            return Err("check_interval_seconds must be greater than 0".to_string());
        }
        Ok(())
    }
}

async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("Failed to install Ctrl+C handler!");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("Failed to install signal handler!")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }
}

fn load_config() -> Result<Config, String> {
    let config_str = fs::read_to_string("Config.toml")
        .map_err(|e| format!("Failed to read Config.toml: {}", e))?;

    toml::from_str(&config_str)
        .map_err(|e| format!("Failed to parse Config.toml: {}", e))
}

fn setup_api_routes(
    node_manager: Arc<Mutex<NodeManager>>,
    api_token: String
) -> impl Filter<Extract = impl Reply> + Clone {
    let with_auth = warp::header::<String>("authorization")
        .map(move |token: String| {
            if token == format!("Bearer {}", api_token) {
                Ok(())
            } else {
                Err(warp::reject::custom(AuthError))
            }
        })
        .and_then(|result: Result<(), _>| async move {
            result.map_err(|_| warp::reject::custom(AuthError))
        });

    let status_route = warp::path("status")
        .and(warp::get())
        .and(with_auth.clone())
        .and(with_node_manager(node_manager.clone()))
        .and_then(handle_status);

    let restart_route = warp::path!("shards" / usize / "restart")
        .and(warp::post())
        .and(with_auth)
        .and(with_node_manager(node_manager))
        .and_then(handle_restart_shard);

    status_route.or(restart_route)
        .with(warp::cors())
        .recover(handle_rejection)
}

fn with_node_manager(node_manager: Arc<Mutex<NodeManager>>) -> impl Filter<Extract = (Arc<Mutex<NodeManager>>,), Error = std::convert::Infallible> + Clone {
    warp::any().map(move || node_manager.clone()) 
}

async fn handle_status(_: (), node_manager: Arc<Mutex<NodeManager>>) -> Result<impl Reply, warp::Rejection> {
    let mut manager = node_manager.lock().unwrap();
    let status = manager.status();
    Ok(warp::reply::json(&status))
}

async fn handle_restart_shard(id: usize, _: (), node_manager: Arc<Mutex<NodeManager>>) -> Result<impl Reply, warp::Rejection> {
    let mut manager = node_manager.lock().unwrap();
    match manager.restart_shard(id) {
        Ok(_) => Ok(warp::reply::json(&format!("Shard {} restarted successfully", id))),
        Err(e) => Err(warp::reject::custom(ApiError(e))),
    }
}

async fn handle_rejection(err: warp::Rejection) -> Result<impl Reply, std::convert::Infallible> {
    let (code, message) = if err.is_not_found() {
        (404, "Not Found".to_string())
    } else if let Some(AuthError) = err.find() {
        (401, "Unauthorized".to_string())
    } else if let Some(ApiError(msg)) = err.find() {
        (400, msg.clone())
    } else {
        (500, "Internal Server Error".to_string())
    };

    let json = warp::reply::json(&HashMap::from([
        ("error", message),
    ]));

    Ok(warp::reply::with_status(json, warp::http::StatusCode::from_u16(code).unwrap()))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = load_config()?;

    let node_manager = Arc::new(Mutex::new(NodeManager::new(&config)));

    {
        let mut manager = node_manager.lock().unwrap();
        for &shard_id in &config.sharding.shards {
            if let Err(e) = manager.add_shard(shard_id) {
                eprintln!("Failed to add shard {}: {}", shard_id, e);
            }
        }
    }

    let monitor_manager = Arc::clone(&node_manager);
    let check_interval = Duration::from_secs(config.monitoring.check_interval_seconds);
    let monitoring_thread = thread::spawn(move || {
        loop {
            thread::sleep(check_interval);

            let mut manager = match monitor_manager.lock() {
                Ok(guard) => guard,
                Err(e) => {
                    error!("Failed to acquire lock: {}", e);
                    continue;
                }
            };
            manager.monitor_shards();
        }
    });

    let rt = Runtime::new()?;

    let server_node_manager = Arc::clone(&node_manager);
    let server_handle = rt.spawn(async move {
        let addr = format!("{}:{}", config.server.host, config.server.port)
            .parse::<std::net::SocketAddr>()
            .expect("Invalid server address");

        println!("Starting API server on {}", addr);
    
        let routes = setup_api_routes(server_node_manager, config.server.token);
        warp::serve(routes).run(addr).await;
    });

    rt.block_on(async {
        tokio::select! {
            _ = server_handle => {},
            _ = shutdown_signal() => {
                println!("Shutdown signal received");
            },
        }
    });

    monitoring_thread.join().expect("Monitor thread panicked");

    let mut manager = node_manager.lock().unwrap();
    manager.stop_all();

    Ok(())
}
