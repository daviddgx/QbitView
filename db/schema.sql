CREATE TABLE IF NOT EXISTS cameras (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    stream_url TEXT NOT NULL,
    location VARCHAR(255) NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cameras_name (name)
);

CREATE TABLE IF NOT EXISTS events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    camera_id BIGINT NOT NULL,
    event_type ENUM('SMOKE', 'FIRE') NOT NULL,
    severity ENUM('PRE_ALERTA', 'CRITICA') NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    message VARCHAR(255) NOT NULL,
    detector_source VARCHAR(40) NOT NULL DEFAULT 'unknown',
    snapshot_path VARCHAR(255) NULL,
    frame_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_events_camera FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE,
    INDEX idx_events_camera_time (camera_id, created_at)
);
