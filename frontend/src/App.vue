<template>
  <div id="app">
    <h1>Churn Prediction</h1>
    <form @submit.prevent="handlePredict">
      <label>Customer ID: <input v-model.number="customer.CustomerID" type="number" readonly /></label>
      <label>Age: <input v-model.number="customer.Age" type="number" required /></label>
      <label>Gender:
        <select v-model="customer.Gender" required>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
        </select>
      </label>
      <label>Tenure: <input v-model.number="customer.Tenure" type="number" required /></label>
      <label>Usage Frequency: <input v-model.number="customer.Usage_Frequency" type="number" required /></label>
      <label>Support Calls: <input v-model.number="customer.Support_Calls" type="number" required /></label>
      <label>Payment Delay: <input v-model.number="customer.Payment_Delay" type="number" required /></label>
      <label>Subscription Type:
        <select v-model="customer.Subscription_Type" required>
          <option value="Basic">Basic</option>
          <option value="Standard">Standard</option>
          <option value="Premium">Premium</option>
        </select>
      </label>
      <label>Contract Length:
        <select v-model="customer.Contract_Length" required>
          <option value="Monthly">Monthly</option>
          <option value="Quarterly">Quarterly</option>
          <option value="Annual">Annual</option>
        </select>
      </label>
      <label>Total Spend: <input v-model.number="customer.Total_Spend" type="number" step="0.01" required /></label>
      <label>Last Interaction: <input v-model.number="customer.Last_Interaction" type="number" required /></label>
      <button type="submit">Predict</button>
    </form>

    <div v-if="result !== null">
      <h2>Prediction Result:</h2>
      <p>Churn: {{ result.churn ? 'Yes' : 'No' }}</p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      customer: {
        CustomerID: Math.floor(Math.random() * 10000),  // Randomly generated Customer ID
        Age: null,
        Gender: "",
        Tenure: null,
        Usage_Frequency: null,
        Support_Calls: null,
        Payment_Delay: null,
        Subscription_Type: "",
        Contract_Length: "",
        Total_Spend: null,
        Last_Interaction: null,
      },
      result: null,
    };
  },
  methods: {
    async handlePredict() {
      try {
        const response = await axios.post("https://super-duper-space-robot-579w4pjvwww345p5-8000.app.github.dev/predict", this.customer);
        this.result = response.data; // Save prediction result
      } catch (error) {
        console.error("Error making prediction:", error);
        this.result = { churn: null }; // Handle errors gracefully
      }
    },
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  margin: 20px;
}
form {
  display: flex;
  flex-direction: column;
  max-width: 400px;
  margin: 0 auto;
}
label {
  margin-bottom: 10px;
}
button {
  margin-top: 20px;
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
button:hover {
  background-color: #369972;
}
</style>
