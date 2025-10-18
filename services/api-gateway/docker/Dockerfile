FROM kong:3.4

# Copy Kong configuration
COPY ./app/kong.yaml /usr/local/kong/declarative/kong.yaml

# Set environment variables
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/usr/local/kong/declarative/kong.yaml
ENV KONG_PROXY_ACCESS_LOG=/dev/stdout
ENV KONG_ADMIN_ACCESS_LOG=/dev/stdout
ENV KONG_PROXY_ERROR_LOG=/dev/stderr
ENV KONG_ADMIN_ERROR_LOG=/dev/stderr
ENV KONG_ADMIN_LISTEN=0.0.0.0:8001
ENV KONG_ADMIN_GUI_URL=http://localhost:8002

# Install plugins
RUN luarocks install kong-prometheus-plugin

# Expose ports
EXPOSE 8000 8001 8443 8444

# Use Kong's default entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

# Use Kong's default command
CMD ["kong", "docker-start"]
