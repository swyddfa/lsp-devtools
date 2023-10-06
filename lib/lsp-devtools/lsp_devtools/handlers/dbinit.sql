-- Tables

-- We use a single table 'protocol' to store all messages sent between client and server.
-- Data within the table is then exposed through a number of SQL views, that parse out the
-- details relevant to that view.
CREATE TABLE IF NOT EXISTS protocol (
    session TEXT,
    timestamp REAL,
    source TEXT,

    id TEXT NULL,
    method TEXT NULL,
    params TEXT NULL,
    result TEXT NULL,
    error TEXT NULL
);

-- Views

-- Requests
CREATE VIEW IF NOT EXISTS requests AS
SELECT
    client.session,
    client.timestamp,
    (server.timestamp - client.timestamp) * 1000 as duration,
    client.id,
    client.method,
    client.params,
    server.result,
    server.error
FROM protocol as client
INNER JOIN protocol as server ON
    client.session = server.session AND
    client.id = server.id AND
    client.params IS NOT NULL AND
    (
        server.result IS NOT NULL OR
        server.error IS NOT NULL
    );

-- Notifications
CREATE VIEW IF NOT EXISTS notifications AS
SELECT
    rowid,
    session,
    timestamp,
    source,
    method,
    params
FROM protocol
WHERE id is NULL;

-- Sessions
CREATE VIEW IF NOT EXISTS sessions AS
SELECT
    session,
    timestamp,
    json_extract(params, "$.clientInfo.name") as client_name,
    json_extract(params, "$.clientInfo.version") as client_version,
    json_extract(params, "$.rootUri") as root_uri,
    json_extract(params, "$.workspaceFolders") as workspace_folders,
    params,
    result
FROM requests WHERE method = 'initialize';

-- Log Messages
CREATE VIEW IF NOT EXISTS logMessages AS
SELECT
    rowid,
    session,
    timestamp,
    json_extract(params, "$.type") as type,
    json_extract(params, "$.message") as message
FROM protocol
WHERE method = 'window/logMessage';
