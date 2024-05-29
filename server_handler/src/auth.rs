// auth.rs

use std::env;

pub fn is_valid_key(key: &str) -> bool {
    match env::var("DISCORD_BOT_TOKEN") {
        Ok(value) => key == value,
        Err(_) => {
            eprintln!("DISCORD_BOT_TOKEN environment variable not found");
            false
        }
    }
}
