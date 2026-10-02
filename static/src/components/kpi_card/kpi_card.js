/** @odoo-module **/
import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "smart_employee_performance_management.KpiCard";
    static props = ["title", "value"];
}