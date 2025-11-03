# Dockerfile Migration Checklist

This checklist guides you through migrating a service to the standardized multi-stage Docker build pattern with Python 3.12 and UV package manager.

## Pre-Migration

- [ ] **Backup current Dockerfile**: Copy existing Dockerfile to `Dockerfile.old` for reference
- [ ] **Review service dependencies**: Check `pyproject.toml` for any special requirements
- [ ] **Identify system dependencies**: Note any system packages needed (e.g., libpq-dev, libxml2-dev)
- [ ] **Check current Python version**: Note the current version in `.python-version`
- [ ] **Document current image size**: Run `docker images | grep <service-name>` and record size

## Python Version Update

- [ ] **Update .python-version**: Change to `3.12`
- [ ] **Update pyproject.toml**: Set `requires-python = ">=3.12"`
- [ ] **Run uv sync locally**: Execute `uv sync` to update `uv.lock` with Python 3.12
- [ ] **Test locally**: Run service locally with Python 3.12 to catch any compatibility issues
- [ ] **Check for deprecation warnings**: Review logs for any Python 3.12 compatibility issues

## Dockerfile Migration

- [ ] **Copy template**: Copy `.kiro/templates/Dockerfile.template` to service directory
- [ ] **Rename to Dockerfile**: Replace existing Dockerfile (after backing up)
- [ ] **Customize builder stage**:
  - [ ] Add any required build-time system dependencies
  - [ ] Verify `pyproject.toml` and `uv.lock` are copied
  - [ ] Confirm `uv sync --frozen --no-dev` command is correct
- [ ] **Customize runtime stage**:
  - [ ] Add any required runtime system dependencies
  - [ ] Verify correct source code paths are copied
  - [ ] Set appropriate port in EXPOSE directive
  - [ ] Configure health check command (if applicable)
  - [ ] Set correct CMD for service entry point
- [ ] **Review environment variables**: Ensure all required ENV vars are set
- [ ] **Create/update .dockerignore**: Exclude unnecessary files from build context

## Service-Specific Customizations

### API Services (FastAPI, Flask)
- [ ] Expose appropriate port (typically 8000)
- [ ] Add health check endpoint verification
- [ ] Use uvicorn or gunicorn in CMD
- [ ] Install curl for health checks

### Worker Services
- [ ] No EXPOSE needed (unless health check port)
- [ ] Set appropriate CMD for worker script
- [ ] Consider adding health check HTTP server

### Services with Special Dependencies

#### Database Clients (psycopg2)
- [ ] Builder: Install `libpq-dev`
- [ ] Runtime: Install `libpq5`

#### XML Processing (lxml)
- [ ] Builder: Install `libxml2-dev libxslt-dev build-essential`
- [ ] Runtime: Install `libxml2 libxslt1.1`

#### Web Scraping (selenium, aria2)
- [ ] Runtime: Install `aria2` or selenium dependencies
- [ ] Consider using specialized base images

## Build and Test

- [ ] **Build image locally**: `docker build -t <service-name>:test .`
- [ ] **Check build output**: Verify both stages complete successfully
- [ ] **Measure image size**: Compare with pre-migration size
- [ ] **Inspect image layers**: `docker history <service-name>:test`
- [ ] **Test container startup**: `docker run --rm <service-name>:test`
- [ ] **Test with docker-compose**: `docker-compose up <service-name>`
- [ ] **Verify service functionality**: Run basic smoke tests
- [ ] **Check logs**: Ensure no Python version warnings or errors
- [ ] **Test health check**: Verify health check endpoint responds (if applicable)

## Integration Testing

- [ ] **Test with dependent services**: Start full stack with docker-compose
- [ ] **Verify database connectivity**: Check service can connect to PostgreSQL
- [ ] **Verify message queue**: Check RabbitMQ integration (if applicable)
- [ ] **Verify storage**: Check MinIO integration (if applicable)
- [ ] **Run integration tests**: Execute service-specific integration tests
- [ ] **Monitor resource usage**: Check memory and CPU usage patterns

## Documentation

- [ ] **Update service README**: Document Python 3.12 and UV requirements
- [ ] **Document build command**: Add docker build instructions
- [ ] **Document environment variables**: List all required ENV vars
- [ ] **Update docker-compose.yml**: Ensure service configuration is correct
- [ ] **Add troubleshooting notes**: Document any service-specific issues encountered

## Performance Validation

- [ ] **Record new image size**: Compare with baseline
- [ ] **Measure build time**: Time the build with and without cache
- [ ] **Test startup time**: Measure container startup duration
- [ ] **Verify layer caching**: Rebuild and check cache hit rate
- [ ] **Document improvements**: Record size reduction and build time improvements

## Rollback Plan

- [ ] **Tag old image**: `docker tag <service-name>:latest <service-name>:pre-migration`
- [ ] **Keep Dockerfile.old**: Retain backup for quick rollback
- [ ] **Document rollback steps**: Note how to revert if issues arise
- [ ] **Test rollback**: Verify old Dockerfile still works if needed

## Post-Migration

- [ ] **Remove Dockerfile.old**: Clean up backup after successful migration
- [ ] **Update CI/CD**: Update build pipelines if applicable
- [ ] **Monitor production**: Watch for any issues in deployed environment
- [ ] **Share learnings**: Document any issues or tips for other services
- [ ] **Update migration guide**: Add service-specific notes to main guide

## Common Issues and Solutions

### Issue: UV sync fails with dependency conflicts
**Solution**: 
- Delete `uv.lock` and run `uv sync` fresh
- Check for Python 3.12 incompatible packages
- Review dependency version constraints in `pyproject.toml`

### Issue: Runtime fails with "module not found"
**Solution**:
- Verify all source directories are copied in runtime stage
- Check PATH includes `/app/.venv/bin`
- Ensure `--no-dev` flag is appropriate for your use case

### Issue: Image size didn't decrease
**Solution**:
- Verify multi-stage build is working (check COPY --from=builder)
- Remove unnecessary system packages
- Check .dockerignore excludes build artifacts
- Ensure build dependencies aren't in runtime stage

### Issue: Service fails to start
**Solution**:
- Check logs: `docker logs <container-id>`
- Verify environment variables are set
- Test locally with same Python version
- Check file permissions in container

### Issue: Health check fails
**Solution**:
- Verify health check command is correct
- Ensure required tools (curl) are installed in runtime
- Check service actually starts before health check
- Adjust health check timing parameters

## Service Migration Order

Follow this recommended order to minimize risk:

1. **company-catalog** - Simplest service, good starting point
2. **ingestion** - Depends on company-catalog
3. **embeddings** - Depends on ingestion
4. **extraction** - Depends on embeddings
5. **api-gateway** - Depends on all data services
6. **airflow** - Orchestrates all services (special case)
7. **db-init** - Infrastructure component

## Success Criteria

Migration is successful when:
- ✅ Service builds without errors
- ✅ Service starts and runs correctly
- ✅ All integration tests pass
- ✅ Image size is reduced by 20-40%
- ✅ No Python version warnings in logs
- ✅ Health checks pass (if applicable)
- ✅ Service integrates with other components
- ✅ Documentation is updated

## Notes

- Take your time with each service
- Test thoroughly before moving to the next
- Document any service-specific issues
- Ask for help if you encounter blockers
- Celebrate small wins! 🎉
