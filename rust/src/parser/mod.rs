#[allow(clippy::module_inception)]
mod core;
pub use self::core::ToonParser;

#[cfg(test)]
mod tests;
