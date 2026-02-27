#!/bin/bash
# Milimo Quantum — Keycloak Initialization

echo "============================================="
echo "🔑 Initializing Keycloak configuration..."
echo "============================================="

# 1. Login to Keycloak Admin CLI inside the container
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin

echo "⏳ Creating milimo-realm..."
# 2. Create Realm (sslRequired=none is important for local dev)
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh create realms -s realm=milimo-realm -s enabled=true -s sslRequired=none || echo "Realm already exists, skipping."

echo "⏳ Creating milimo-client..."
# 3. Create Client
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh create clients -r milimo-realm \
    -s clientId=milimo-client \
    -s enabled=true \
    -s publicClient=true \
    -s standardFlowEnabled=true \
    -s directAccessGrantsEnabled=true \
    -s implicitFlowEnabled=true \
    -s 'redirectUris=["http://localhost:5173/*", "http://localhost:8000/*", "http://localhost:5173", "http://localhost:5173/"]' \
    -s 'webOrigins=["+", "http://localhost:5173", "http://localhost:8000"]' || echo "Client already exists, skipping."

echo "⏳ Creating admin user..."
# 4. Create User
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh create users -r milimo-realm \
    -s username=admin \
    -s enabled=true \
    -s email=admin@milimo.local \
    -s firstName=Admin \
    -s lastName=User || echo "User already exists, skipping."

echo "⏳ Setting password for admin user..."
# 5. Set Password
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh set-password -r milimo-realm --username admin --new-password admin

echo "============================================="
echo "🎉 Keycloak configuration complete!"
echo "   You can now log in to the application."
echo "   Username: admin"
echo "   Password: admin"
echo "============================================="
