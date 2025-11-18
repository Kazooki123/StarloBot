use std::fmt;
use warp::reject::Reject;

#[derive(Debug, thiserror::Error)]
pub enum BotError {
    #[error("Process error: {0}")]
    ProcessError(#[from] std::io::Error),
    
    #[error("Invalid shard configuration: {0}")]
    ShardError(String),
    
    #[error("Configuration error: {0}")]
    ConfigError(String),
    
    #[error("Runtime error: {0}")]
    RuntimeError(String),
    
    #[error("Lock acquisition failed: {0}")]
    LockError(String),
}

#[derive(Debug)]
pub struct AuthError;
impl Reject for AuthError {}

#[derive(Debug)]
pub struct ApiError(pub String);
impl Reject for ApiError {}

impl fmt::Display for AuthError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Unauthorized")
    }
}

impl std::error::Error for AuthError {}