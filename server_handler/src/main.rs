extern crate actix_web;
extern crate serde;

use actix_web::{get, post, web, App, HttpResponse, HttpServer};
use serde::Deserialize;

#[derive(Deserialize)]
struct LevelRequest {
    user_id: u64,
    level: u32,
}

#[post("/update_level")]
fn update_level(req: web::Json<LevelRequest>) -> HttpResponse {
    println!("Received level update for user {}: level {}", req.user_id, req.level);
    HttpResponse::Ok().json("Level updated")
}

#[get("/health_check")]
fn health_check() -> HttpResponse {
    HttpResponse::Ok().json("Server is running")
}

#[actix_web::main] // Switch back to this for async handling
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .service(update_level)
            .service(health_check)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}