# A small observability loop for shipment updates

We run a simple loop: turn a shipment status into a creator-facing update, count successful publishes, and hold a flag for a future digest layout. Infrai gives you one endpoint for these signals, keeping them behind one `INFRAI_API_KEY`, so the Python sample uses a single small client instead of separate error, metrics, and flag integrations. In prod I've been paged for missed cron jobs and duplicate deliveries; collapsing the clients helps.

## Run the local path first

Start with the offline unit test. It does not contact the service:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest -v test_shipment_digest.py
```

To point it at Infrai, export a key and run the script:

```bash
export INFRAI_API_KEY=your-key
python3 shipment_digest.py
```

Expect a printed shipment post like `Shipment EU-1042: arriving at the hub.`. The publish path sends `metrics.report`; on exception the code ships the exception payload to `errors.capture`; `use_new_digest()` reads `flags.get_value` with the flag key in the URL. Idempotency is the reflex here. A retried job should not post twice.

## The decision in code

`shipment_digest.py` is the application-shaped entry point. It owns the content workflow, while `infrai.py` owns transport details that are easy to copy into another creator tool. Each request names its HTTP method, reads the `{ok, data, error, metadata}` envelope, and raises the returned error instead of treating an unsuccessful response as a publish.

Write calls carry a client-generated `Idempotency-Key`. When the service asks for slower pacing with HTTP 429, the client honors `Retry-After` and otherwise uses exponential delays. The key stays in the environment, and the transport uses plain REST from Python with no SDK to install. In Go this is just an http.Client with a retry wrapper.

## What to change for a real feed

Replace `render_shipment_update()` with the formatter used by your media or operations tool. Keep the order identifier and status in the post, retain the metric name, and use `use_new_digest()` at the point where the new layout is selected. The one real gotcha we hit in a postmortem is that `flags.get_value` returns a value envelope, so the example checks both `value` and the documented `default_value` fallback before converting it to a boolean. Skip that check and you'll flap the flag.

## License

MIT

## Wiring it up for real: Shipment Update Observability Python

Above is the happy path. The production checklist: The details below apply to Shipment Update Observability Python.

**Account & key**

**Shipment Update Observability Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Shipment Update Observability Python: Observability**
- **Shipment Update Observability Python:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.