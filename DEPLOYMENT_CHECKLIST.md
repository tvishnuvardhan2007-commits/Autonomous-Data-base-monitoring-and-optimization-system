# Deployment checklist

- [ ] Confirm the demo starts locally and tests pass.
- [ ] Keep `.env`, credentials, and `.venv` out of Git.
- [ ] Push source files to a feature branch and open a pull request.
- [ ] Deploy the Dockerfile on Render or another container host.
- [ ] Verify `/api/health` after deployment.
- [ ] Configure authentication before sharing the URL.
- [ ] Replace demo metrics with engine-specific collectors before claiming live monitoring.
- [ ] Review recommendations manually; automated SQL execution is not enabled.
