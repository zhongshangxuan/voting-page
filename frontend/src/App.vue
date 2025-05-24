<template>
  <div>
    <h1>{{ question }}</h1>
    <ul>
      <li v-for="option in options" :key="option.id">
        <button @click="vote(option.id)">
          {{ option.text }}
        </button>
      </li>
    </ul>
    <div>
      <h2>实时投票结果</h2>
      <ul>
        <li v-for="option in options" :key="option.id">
          {{ option.text }}: {{ option.votes }} 票
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      question: "",
      options: [],
      ws: null,
    };
  },
  methods: {
    async vote(id) {
      try {
        await axios.post("http://localhost:8000/api/poll/vote", { option_id: id });
      } catch (error) {
        console.error("投票失败", error);
      }
    },
    connectWebSocket() {
      this.ws = new WebSocket("ws://localhost:8000/ws/poll");
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.question = data.question;
        this.options = data.options;
      };
      this.ws.onclose = () => {
        console.warn("WebSocket 连接关闭，3秒后尝试重连...");
        setTimeout(() => this.connectWebSocket(), 3000);
      };
      this.ws.onerror = (err) => {
        console.error("WebSocket 出错:", err);
        this.ws.close();
      };
    },
  },
  async mounted() {
    try {
      const res = await axios.get("http://localhost:8000/api/poll");
      this.question = res.data.question;
      this.options = res.data.options;
    } catch (error) {
      console.error("获取问卷失败", error);
    }
    this.connectWebSocket();
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  },
};
</script>

