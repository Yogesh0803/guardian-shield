const express = require("express");
const { WebSocketServer } = require("ws");
const app = express();
const PORT = 5000;

// Serve static files from the 'public' folder
app.use(express.static("public"));

const server = app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});

// WebSocket Server Setup
const wss = new WebSocketServer({ server });

// Server configuration
const servers = [
  { id: 'Server 1', baseUsage: 20 },
  // Add more servers if needed
];

const servers1 = [
  { id: 'Server 1', baseUsage: 20, phaseShift: 0 },
  { id: 'Server 2', baseUsage: 30, phaseShift: Math.PI / 3 },
  { id: 'Server 3', baseUsage: 40, phaseShift: 2 * Math.PI / 3 },
  { id: 'Server 4', baseUsage: 50, phaseShift: Math.PI / 2 },
  { id: 'Server 5', baseUsage: 60, phaseShift: 3 * Math.PI / 4 },
];

// Function to generate mock network usage data
function getMockNetworkUsage() {
  const result = {};

  servers.forEach((server) => {
    const baseUsage = server.baseUsage;

    result[server.id] = {
      app1: Math.min(Math.max(baseUsage * Math.random(), 0), 100),
      app2: Math.min(Math.max(baseUsage * Math.random(), 0), 100),
    };
  });

  return result;
}

function getMockNetworkUsage1() {
  const result = {};

  servers1.forEach((server) => {
    const baseUsage = server.baseUsage;

    result[server.id] = {
      app1: Math.min(Math.max(baseUsage * Math.random(), 0), 100),
      app2: Math.min(Math.max(baseUsage * Math.random(), 0), 100),
    };
  });

  return result;
}

// Function to generate mock comparison data with timestamps
function getMockComparison() {
  const normal = [];
  const abnormal = [];
  const networkUsage = getMockNetworkUsage1(); // Get network usage only once

  const currentTime = Date.now();
  const interval = 60000; // 1 minute interval

  Object.keys(networkUsage).forEach((serverId) => {
    // Generate data points for normal and abnormal data with timestamps
    for (let i = 0; i < 10; i++) {
      const timestamp = new Date(currentTime - i * interval).toISOString(); // Create timestamp
      normal.push({
        timestamp,
        serverId,
        value: networkUsage[serverId].app1, // Use consistent data for normal
      });
      abnormal.push({
        timestamp,
        serverId,
        value: networkUsage[serverId].app2, // Use consistent data for abnormal
      });
    }
  });

  return { normal, abnormal };
}

// Function to generate mock application data
function getMockApplications() {
  return [
    {
      serverId: 'Server 1',
      applications: [
        { name: 'App 1', endpoint: '/api/app1', status: 'Running', lastAccessed: '2024-08-30' },
        { name: 'App 2', endpoint: '/api/app2', status: 'Stopped', lastAccessed: '2024-08-28' },
      ],
    },
    // Add more servers and applications as needed
  ];
}

// Function to generate mock alert data
function getMockAlerts() {
  const severities = ['Low', 'Medium', 'High'];
  const descriptions = [
    'Disk space running low',
    'CPU usage exceeded threshold',
    'Network latency high',
    'Service response time increased',
  ];

  return Array.from({ length: 5 }, (_, i) => ({
    alertId: `Alert ${i + 1}`,
    description: descriptions[Math.floor(Math.random() * descriptions.length)],
    severity: severities[Math.floor(Math.random() * severities.length)],
    timestamp: new Date().toISOString(),
  }));
}

// WebSocket connection handling
wss.on("connection", (ws) => {
  console.log("New client connected");

  // Set interval to send data to the client every 500 milliseconds
  const sendDataInterval = setInterval(() => {
    if (ws.readyState === ws.OPEN) {
      try {
        const data = {
          networkUsage: getMockNetworkUsage(),
          applications: getMockApplications(),
          alerts: getMockAlerts(),
          comparison: getMockComparison(), // Add comparison data to the message
        };
        ws.send(JSON.stringify(data));
      } catch (error) {
        console.error("Error sending data:", error);
      }
    }
  }, 500); // Send data every 500 milliseconds (0.5 seconds)

  ws.on("close", () => {
    console.log("Client disconnected");
    clearInterval(sendDataInterval); // Clear interval when client disconnects
  });

  ws.on("error", (error) => {
    console.error("WebSocket error:", error);
  });
});
