# Guardian Shield: Context-Aware ML Firewall 🛡️

[![Smart India Hackathon 2024](https://img.shields.io/badge/Smart%20India%20Hackathon-2024-blue)](https://sih.gov.in/)
[![ISRO](https://img.shields.io/badge/Organization-ISRO-orange)](https://www.isro.gov.in/)

## Project Overview 🚀

Guardian Shield is a context-aware ML firewall developed for the Smart India Hackathon 2024, where our team was among the top 48 finalists selected from over 1000+ teams. The project was showcased at the Grand Finale in Ahmedabad, hosted by ISRO (Indian Space Research Organisation).

The frontend interface provides a robust, user-friendly dashboard for monitoring and controlling network traffic, managing endpoints, and implementing security policies in real-time.

## Key Features ✨

- **Real-time Network Monitoring**: Interactive graphs and visualizations for network traffic analysis
- **Endpoint Management**: Comprehensive interface for managing and monitoring multiple endpoints
- **Policy Configuration**: Intuitive policy creation and deployment system
- **Alert Dashboard**: Real-time alert monitoring with detailed insights
- **Activity Monitoring**: Visual representation of normal vs. abnormal activities
- **DPI (Deep Packet Inspection)**: Advanced packet analysis and visualization

## Technical Architecture 🏗️

The project follows a distributed architecture with three main components:

1. **Frontend (This Repository)**: React-based web console for monitoring and control
2. **Backend**: FastAPI-powered REST service for data processing and policy management
3. **Agent**: Distributed monitoring system using Scapy and TensorFlow for network analysis

## Tech Stack 💻

### Frontend Technologies
- Tailwind CSS for responsive design
- React.js for dynamic UI components
- Chart.js for real-time data visualization

### Backend Integration
- FastAPI for high-performance REST APIs
- MongoDB Atlas for scalable data storage
- AI/ML integration with TensorFlow

## Screenshots 📸

### Login Page
![Screenshot (376)](https://github.com/user-attachments/assets/5cc71552-d593-44bb-88b1-448c2ba5cc11)

### Network Monitoring Dashboard
Real-time anomaly detection and AI-powered threat response with live traffic graphs and automated blocking

![Picture1](https://github.com/user-attachments/assets/e9f4060f-7752-4017-9c8f-021da2b058b3)
![Picture2](https://github.com/user-attachments/assets/e2afb683-7ffa-4cc9-adc3-14e2b1b1dc3e)

### Application Management : 
Displaying application activity details and an alert monitoring system with high-confidence normal activity detection.

![Picture3](https://github.com/user-attachments/assets/0b790bbb-d0c1-429d-b871-8a09c73db759)
![Picture4](https://github.com/user-attachments/assets/3972a105-3493-475c-923f-b730e8c6e7bd)

### Endpoint Management
Centralized Endpoint Management system enabling admins to monitor, deploy policies, and manage applications with detailed endpoint insights

![Picture5](https://github.com/user-attachments/assets/06be4231-624b-4312-abc4-12591e9cae4f)
![Picture6](https://github.com/user-attachments/assets/255f8a7c-26df-4fb9-88b6-93aa89e5dea1)

### Policy Management
Policy Deployment: Enables admins to configure and deploy security policies by specifying IPs, ports, protocols, apps, and actions (block/unblock) for endpoint control.

![Picture9](https://github.com/user-attachments/assets/3f4521bb-dc52-4cd0-ab05-eff14ccabd4f)
![Screenshot (377)](https://github.com/user-attachments/assets/8e9b531c-83b4-475d-be90-29df1fbe07e0)

### DPI Management
Application Monitoring: Shows real-time network usage, activity graphs, and app-specific alerts for endpoint monitoring (Deep Packet Inspection)

![Picture7](https://github.com/user-attachments/assets/a1f16e8e-10b6-4cfd-bc14-888d7bb691a4)
![Picture8](https://github.com/user-attachments/assets/22d41219-c11b-4d50-85a2-b710b21f3000)

## Related Repositories 🔗

- Backend Repository: [Guardian Shield Backend](https://github.com/artifcialmind/Context-Aware-Firewall-SIH-2024/tree/shiwans_backend_code)

## Team VAJRA 🤝

Part of Team VAJRA's submission for Smart India Hackathon 2024, developed under the guidance of ISRO.

## Installation and Setup 🛠️

```bash
# Clone the repository
git clone https://github.com/atulkp018/GuardianShield.git

# Navigate to project directory
cd GuardianShield

# Install dependencies
npm install

# Start development server
npm start
```

## Contributing 🤲

While this project was developed for the Smart India Hackathon, we welcome contributions and suggestions. Feel free to:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Developed with ❤️ by Team VAJRA for Smart India Hackathon 2024*
