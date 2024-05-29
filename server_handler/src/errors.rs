// errors.rs

use actix_web::{HttpResponse, ResponseError};
use std::error::Error;
use std::any::Any;

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("Invalid API key")]
    InvalidApiKey,
    // Add more error variants as needed
}

impl ResponseError for AppError {}

pub fn http_error(err: &impl Error + Any) -> HttpResponse {
    let status_code = match err.downcast_ref::<AppError>() {
        Some(AppError::InvalidApiKey) => actix_web::http::StatusCode::UNAUTHORIZED,
        // Add more mappings as needed
        _ => actix_web::http::StatusCode::INTERNAL_SERVER_ERROR,
    };

    HttpResponse::build(status_code)
        .content_type("text/plain")
        .body(err.to_string())
}
