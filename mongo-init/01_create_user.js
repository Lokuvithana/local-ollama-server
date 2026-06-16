db = db.getSiblingDB('sunrise_hospital');

db.createUser({
  user: "app_user",
  pwd: "app_pass123",
  roles: [{ role: "readWrite", db: "sunrise_hospital" }]
});

print("MongoDB: app_user created for sunrise_hospital database");
