// main.rs

extern crate actix_web;
extern crate serde;

mod auth;
mod errors;

use actix_web::{get, post, web, App, HttpResponse, HttpServer, Responder};
use serde::Deserialize;
use auth::is_valid_key;
use errors::{AppError, http_error, HttpErrorHandler};
use core::error::Error;
use std::any::Any;

#[derive(Deserialize)]
struct LevelRequest {
    user_id: u64,
    level: u32,
    api_key: String,
}

#[post("/update_level")]
async fn update_level(req: web::Json<LevelRequest>) -> Result<HttpResponse, AppError> {
    if !is_valid_key(&req.api_key) {
        return Err(AppError::InvalidApiKey);
    }

    println!("Received level update for user {}: level {}", req.user_id, req.level);
    Ok(HttpResponse::Ok().json("Level updated"))
}

#[get("/health_check")]
async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json("Server is running")
}

struct HttpErrorHandler;

impl Responder for HttpErrorHandler {
    type Error = actix_web::Error;
    type Future = actix_web::error::DefaultErrorResponse;

    fn respond_to(self, req: &actix_web::HttpRequest) -> Self::Future {
        actix_web::error::DefaultErrorResponse::respond_to(self, req)
    }
}

impl<E: Error + Any> actix_web::Handler<E> for HttpErrorHandler {
    type Result = HttpResponse;

    fn call(&self, error: E) -> Self::Result {
        http_error(&error)
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .service(update_level)
            .service(health_check)
            .default_service(web::route().to(HttpErrorHandler))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
