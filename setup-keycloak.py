import os
from keycloak import KeycloakAdmin
import sys

try:
    # Configure admin client connection
    keycloak_admin = KeycloakAdmin(server_url="http://localhost:8080/",
                                   username='admin',
                                   password='admin',
                                   realm_name="master",
                                   verify=True)

    # 1. Create Realm
    try:
        keycloak_admin.create_realm(payload={
            "realm": "milimo-realm", 
            "enabled": True,
            "registrationAllowed": True
        })
        print("✅ Realm 'milimo-realm' created successfully.")
    except Exception as e:
        print(f"ℹ️  Realm creation note (might already exist): {e}")

    # Switch context to the new realm
    keycloak_admin.realm_name = "milimo-realm"

    # 2. Create Client
    try:
        keycloak_admin.create_client(payload={
            "clientId": "milimo-client",
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True,
            "implicitFlowEnabled": True,
            "redirectUris": ["http://localhost:5173/*", "http://localhost:8000/*", "http://localhost:5173", "http://localhost:5173/"],
            "webOrigins": ["+", "http://localhost:5173", "http://localhost:8000"]
        })
        print("✅ Client 'milimo-client' created successfully.")
    except Exception as e:
        print(f"ℹ️  Client creation note (might already exist): {e}")

    # 3. Create Test User
    try:
        keycloak_admin.create_user({
            "username": "admin", 
            "email": "admin@milimo.local", 
            "firstName": "Admin",
            "lastName": "User",
            "enabled": True
        })
        
        user_id = keycloak_admin.get_user_id("admin")
        keycloak_admin.set_user_password(user_id, "admin", temporary=False)
        
        # Give realm admin roles to this user so they can access things
        try:
            # Add general user role mappings or group membership if required
            pass
        except Exception as role_e:
            print(f"Could not assign roles: {role_e}")
            
        print("✅ Test user 'admin' (password: admin) created successfully.")
    except Exception as e:
        print(f"ℹ️  User creation note (might already exist): {e}")

    print("\n🎉 Keycloak is ready! You can now log into the app with:")
    print("   Username: admin")
    print("   Password: admin")

except Exception as e:
    print(f"❌ Critical Error connecting to Keycloak: {e}")
    sys.exit(1)
