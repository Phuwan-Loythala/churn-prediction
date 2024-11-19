import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',  // Backend URL
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // Method to call the API
  predictChurn(data) {
    // Log the data being sent to ensure it's correct
    console.log("Sending data to API:", data);
    return apiClient.post("/predict", data);  // Send data to FastAPI
  },
};
