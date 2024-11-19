<template>
  <div>
    <h2>Churn Prediction</h2>
    <form @submit.prevent="submitForm">
      <label>Credit Score:</label>
      <input v-model="customer.credit_score" type="number" required />

      <label>Geography (0 = France, 1 = Germany, 2 = Spain):</label>
      <input v-model="customer.geography" type="number" required />

      <label>Gender (0 = Male, 1 = Female):</label>
      <input v-model="customer.gender" type="number" required />

      <label>Age:</label>
      <input v-model="customer.age" type="number" required />

      <label>Tenure:</label>
      <input v-model="customer.tenure" type="number" required />

      <label>Balance:</label>
      <input v-model="customer.balance" type="number" required />

      <label>Number of Products:</label>
      <input v-model="customer.num_of_products" type="number" required />

      <label>Has Credit Card (0 = No, 1 = Yes):</label>
      <input v-model="customer.has_credit_card" type="number" required />

      <label>Is Active Member (0 = No, 1 = Yes):</label>
      <input v-model="customer.is_active_member" type="number" required />

      <label>Estimated Salary:</label>
      <input v-model="customer.estimated_salary" type="number" required />

      <button type="submit">Predict</button>
    </form>

    <div v-if="result">
      <h3>Prediction Result:</h3>
      <p>Churn: {{ result.churn }}</p>
      <p>Probability: {{ (result.probability * 100).toFixed(2) }}%</p>
    </div>
  </div>
</template>

<script>
// Import the API client
import apiClient from './apiClient';

export default {
  data() {
    return {
      customer: {
        credit_score: null,
        geography: null,
        gender: null,
        age: null,
        tenure: null,
        balance: null,
        num_of_products: null,
        has_credit_card: null,
        is_active_member: null,
        estimated_salary: null,
      },
      result: null,
    };
  },
  methods: {
    async submitForm() {
      try {
        // Check if customer data is valid
        if (Object.values(this.customer).some(val => val === null || val === undefined)) {
          console.error("Please fill in all the fields.");
          return;
        }

        // Log customer data before sending
        console.log("Sending data to API:", this.customer);

        // Call API to predict churn
        const response = await apiClient.predictChurn(this.customer);
        this.result = response.data;  // Update result with prediction

        console.log("Prediction Result:", this.result);  // Log prediction result
      } catch (error) {
        console.error("Error predicting churn:", error);
      }
    },
  },
};
</script>

