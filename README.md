# envoy-cli

> A CLI tool to manage and sync `.env` files across local, staging, and production environments securely.

---

## Installation

```bash
pip install envoy-cli
```

Or install from source:

```bash
git clone https://github.com/yourname/envoy-cli.git && cd envoy-cli && pip install .
```

---

## Usage

Initialize envoy in your project:

```bash
envoy init
```

Push your local `.env` to a remote environment:

```bash
envoy push --env staging
```

Pull the latest `.env` from production:

```bash
envoy pull --env production
```

Compare differences between environments:

```bash
envoy diff --from local --to staging
```

List all tracked variables:

```bash
envoy list
```

---

## How It Works

`envoy-cli` encrypts your `.env` files before syncing them to a configured remote backend (S3, GCS, or a self-hosted store). Each environment is isolated and access-controlled, keeping secrets out of version control.

---

## Configuration

A `.envoy.toml` file in your project root defines your environments and backend:

```toml
[backend]
type = "s3"
bucket = "my-envoy-store"

[environments]
staging = "us-east-1"
production = "us-east-1"
```

---

## License

[MIT](LICENSE) © 2024 yourname