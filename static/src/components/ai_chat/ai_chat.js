/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class AiChatWidget extends Component {
    static template = "smart_employee_performance_management.AiChatWidget";
    static props = [];

    setup() {
        this.state = useState({
            isOpen: false,
            isLoading: false,
            inputMessage: "",
            messages: [
                {
                    role: "assistant",
                    text: "AI Career Assistant active. How can I assist you with performance tracking or promotion readiness?",
                },
            ],
        });
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
    }

    async sendMessage() {
        const query = this.state.inputMessage ? this.state.inputMessage.trim() : "";
        if (!query || this.state.isLoading) {
            return;
        }

        this.state.messages.push({ role: "user", text: query });
        this.state.inputMessage = "";
        this.state.isLoading = true;

        try {
            const res = await rpc("/smart_performance/ai_chat", { prompt: query });
            this.state.messages.push({
                role: "assistant",
                text: (res && (res.reply || res.response)) || "No analysis returned from model.",
            });
        } catch (error) {
            console.error("AI Chat Error:", error);
            this.state.messages.push({
                role: "assistant",
                text: "AI service connection error. Please verify configuration.",
            });
        } finally {
            this.state.isLoading = false;
        }
    }
}