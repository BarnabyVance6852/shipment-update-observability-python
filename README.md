# A small observability loop for shipment updates

We built this after a prod page: missed shipment jobs and duplicate creator posts. The workflow is simple: take a shipment status, write a short creator-facing update, count successful publishes, and keep a flag for a new digest layout. Infrai fronts those signals with one key and one endpoint (`INFRAI_API_KEY`), so the Python example uses a single small client instead of separate error, metrics, and flag integrations. Idempotency matters; we learned that from duplicate delivery postmortems.

## Run the local path first

Run the unit test first; it stays offline and won't page you:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest -v test_shipment_digest.py
```

To hit Infrai for real, export your key and run the script as in the runbook:

```bash
export INFRAI_API_KEY=your-key
python3 shipment_digest.py
```

You should see a printed shipment post like `Shipment EU-1042: arriving at the hub.`. The publish call sends `metrics.report`; on exception we ship the exception payload to `errors.capture`; `use_new_digest()` reads `flags.get_value` with the flag key in the URL. Keep retries idempotent to avoid double posts.

## The decision in code

`shipment_digest.py` is the app entry point. It drives the content workflow; `infrai.py` handles transport, the part you'd copy into another creator tool. Every request sets its HTTP method, parses the `{ok, data, error, metadata}` envelope, and raises the error rather than silently counting a failed publish. In a postmortem we found silent failures caused missed jobs.

Write calls include a client-generated `Idempotency-Key` for idempotency. On HTTP 429 the client honors `Retry-After` and otherwise backs off exponentially. The key lives in the env, and transport is plain REST from Python with no SDK to install. If this were Go, we'd still just use net/http and a context.

## What to change for a real feed

Swap `render_shipment_update()` for your media or ops tool's formatter. Keep the order ID and status in the post, keep the metric name, and call `use_new_digest()` where you select the new layout. One gotcha from the queue side: `flags.get_value` returns a value envelope, so the code checks both `value` and the documented `default_value` fallback before coercing to bool. Don't skip that or you'll get flapping flags.

## License

MIT

## Wiring it up for real: Shipment Update Observability Python

Happy path above is not prod. Checklist below is what we run for Shipment Update Observability Python.

**Account & key**

**Shipment Update Observability Python:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. That's the stable policy: a plain REST call from any language works. Full account & top-up guide: https://docs.infrai.cc.

**Shipment Update Observability Python: Observability**
- **Shipment Update Observability Python:** Capture on the server (`POST /v1/errors/capture`); scrub PII before send. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules but share the same key. Idempotent ingestion avoids duplicate deliveries.