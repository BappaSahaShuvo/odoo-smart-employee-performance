/** @odoo-module **/
import { Component, useState, onWillStart, onWillDestroy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { AiChatWidget } from "../components/ai_chat/ai_chat";

export function generateInitialCalendarDays() {
    const days = [];
    // 2 empty slots for Sunday/Monday (Sept 1, 2026 starts on Tuesday)
    days.push({ day: '', status: 'empty', is_today: false, check_in: '', check_out: '', late_mins: 0, status_label: '' });
    days.push({ day: '', status: 'empty', is_today: false, check_in: '', check_out: '', late_mins: 0, status_label: '' });
    for (let i = 1; i <= 30; i++) {
        const dayOfWeek = (i + 1) % 7; // 5=Fri, 6=Sat
        const isWeekend = (dayOfWeek === 5 || dayOfWeek === 6);
        const isToday = (i === 6); // Today is 06 Sept 2026
        let st = 'future';
        let cin = '', cout = '', lm = 0;
        if (isWeekend) {
            st = 'weekend';
        } else if (i < 6) {
            st = (i === 3) ? 'late' : 'present';
            cin = (i === 3) ? '09:25 AM' : '08:58 AM';
            cout = '05:15 PM';
            lm = (i === 3) ? 25 : 0;
        } else if (isToday) {
            st = 'present';
            cin = '09:00 AM';
            cout = 'Still in';
        }
        days.push({
            day: i,
            status: st,
            is_today: isToday,
            check_in: cin,
            check_out: cout,
            late_mins: lm,
            status_label: st.charAt(0).toUpperCase() + st.slice(1)
        });
    }
    return days;
}

export function getDefaultDashboardData() {
    return {
        departments: [],
        kpis: {
            total_employees: 0,
            active_employees: 0,
            number_of_leave: 0,
            new_employees: 0,
            happiness_rate: 0,
            promotion_candidates: 0,
            active_warnings: 0,
            turnover_rate: 0,
            avg_company_kpi: 0,
            training_completion_rate: 0,
            rewards_issued: 0,
            team_score: 0,
            pending_goals: 0,
            pending_reviews: 0,
            high_risk_employees: 0,
            avg_attendance: 0,
            team_attendance: 0,
            goal_progress: 0,
            tasks_completed: 0,
            avg_kpi: 0,
            team_warnings: 0,
            kpi_score: 0,
            attendance_pct: 0,
            goal_progress_pct: 0,
            training_progress_pct: 0,
            reward_count: 0,
            warning_count: 0,
            overtime_hours: 0,
            on_time_pct: 0,
            present_today: 0,
            absent_today: 0,
        },
        ai_kpis: {
            promo_probability: 0,
            flight_risk_count: 0,
            burnout_risk_score: 0,
            skill_gap_score: 0,
            ai_confidence: 0,
        },
        punctuality_pie: {
            on_time_count: 0,
            on_time_pct: 0,
            late_count: 0,
            late_pct: 0,
        },
        charts: {
            dept_performance: { labels: [], data: [] },
            trend_line: { labels: [], data: [] },
            working_format: { remote: 0, onsite: 0 },
            staff_turnover: { labels: [], data: [] },
            attrition_heatmap: [],
            attendance_trend: { labels: [], data: [] },
            lateness_trend: { labels: [], data: [] },
            leave_distribution: [],
            goal_completion: [],
            performance_dist: { labels: [], data: [] },
            working_hours: { labels: [], data: [] },
            daily_kpi: { labels: [], data: [] },
            radar_skills: [],
            attendance_calendar: [],
        },
        tables: {
            top_performers: [],
            bottom_performers: [],
            pipeline: [],
            warning_requests: [],
            promotion_requests: [],
            trainings: [],
            pending_goals: [],
            pending_reviews: [],
            team_members: [],
            today_attendance: [],
            goal_approvals: [],
        },
        goals: [],
        trainings: [],
        rewards: [],
        warnings: [],
        skills: [],
        heatmap: [],
        skill_gaps: [],
        recommendations: [],
        reports_data: [],
        nine_box: [],
        my_leaves: [],
        pending_leave_approvals: [],
        leave_balances: {
            casual: { available: 12, total: 12 },
            sick: { available: 14, total: 14 },
            yearly: { available: 10, total: 10 },
            unpaid: { available: 170, total: 170 },
        },
        career_path: { current_role: '', target_role: '', match_pct: 0, steps: [] },
        employee_profile: {
            id: null,
            name: '',
            employee_code: '',
            designation: '',
            department: '',
            email: '',
            personal_phone: '',
            official_phone: '',
            company: '',
            employment_status: '',
            joining_date: '',
            service_length: '',
            supervisor: '',
            dotted_supervisor: '',
            line_manager: '',
            shift: '',
            greeting: '',
            is_eligible_promotion: false,
        },
        attendance_widget: {
            employee_name: '',
            today_date_str: '06 Sept 2026',
            hours_display: '03:45',
            check_in_time: '09:00 AM',
            check_out_time: 'Still in',
            is_checked_in: true,
            current_status: 'WORKING (CHECKED IN)',
            button_label: 'PUNCH OUT',
            button_class: 'btn-danger',
            year: 2026,
            month: 9,
            month_name: 'September',
            salary_deductions_days: 0,
            summary: { payable_days: 22, present: 3, late: 1, movement: 0, leave: 0, absent: 0 },
            calendar_days: generateInitialCalendarDays()
        },
        ai_summary: '',
        ai_notice: false,
    };
}

export class SmartPerformanceDashboard extends Component {
    static template = "smart_employee_performance_management.MainDashboard";
    static components = { AiChatWidget };
    static props = ["*"];

    setup() {
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            isLoggedIn: false,
            loginForm: {
                username: "admin",
                password: "admin"
            },
            loginErrorMessage: "",
            activeRole: "admin",
            activeEmployeeId: null,
            activeEmployeeName: "Administrator",
            activeTab: "ceo",
            selectedDept: "all",
            calYear: 2026,
            calMonth: 9,
            currentTimeStr: "12:06:20 PM",
            currentDateStr: "06 Sept 2026",
            data: getDefaultDashboardData(),
            loading: false,
            leaveApplyForm: {
                leave_type: "casual",
                date_from: new Date().toISOString().split('T')[0],
                date_to: new Date().toISOString().split('T')[0],
                reason: ""
            }
        });

        this._timer = setInterval(() => {
            const now = new Date();
            this.state.currentTimeStr = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });
        }, 1000);

        onWillStart(async () => {
            // Prepared for user login
        });

        onWillDestroy(() => {
            if (this._timer) clearInterval(this._timer);
        });
    }

    async performLogin() {
        this.state.loginErrorMessage = "";
        try {
            const res = await rpc("/smart_performance/login", {
                login: this.state.loginForm.username,
                password: this.state.loginForm.password
            });

            if (res && res.status === "success") {
                this.state.isLoggedIn = true;
                this.state.activeRole = res.role;
                this.state.activeEmployeeId = res.employee_id;
                this.state.activeEmployeeName = res.employee_name;

                if (res.role === "admin" || res.role === "ceo") this.state.activeTab = "ceo";
                else if (res.role === "hr") this.state.activeTab = "hr";
                else if (res.role === "manager") this.state.activeTab = "manager";
                else if (res.role === "team_leader") this.state.activeTab = "team_leader";
                else this.state.activeTab = "employee";

                await this.loadData(this.state.activeTab);
            } else {
                this.state.loginErrorMessage = (res && res.message) || "Invalid credentials.";
            }
        } catch (err) {
            this.state.loginErrorMessage = "Authentication service offline.";
        }
    }

    performLogout() {
        this.state.isLoggedIn = false;
        this.state.data = getDefaultDashboardData();
    }

    quickDemoLogin(user, pwd) {
        this.state.loginForm.username = user;
        this.state.loginForm.password = pwd;
        this.performLogin();
    }

    async switchTab(tabKey) {
        this.state.loading = true;
        this.state.activeTab = tabKey;
        await this.loadData(tabKey);
    }

    async onDeptChange(ev) {
        this.state.loading = true;
        this.state.selectedDept = ev.target.value;
        await this.loadData(this.state.activeTab);
    }

    async loadData(tabKey) {
        try {
            const res = await rpc("/smart_performance/dashboard_data", {
                dashboard_type: tabKey,
                filters: {
                    department_id: this.state.selectedDept,
                    year: this.state.calYear,
                    month: this.state.calMonth
                },
                active_role: this.state.activeRole,
                target_employee_id: this.state.activeEmployeeId
            });
            if (res) {
                const defaults = getDefaultDashboardData();
                const safeCalendarDays = (res.attendance_widget && res.attendance_widget.calendar_days && res.attendance_widget.calendar_days.length)
                    ? res.attendance_widget.calendar_days
                    : defaults.attendance_widget.calendar_days;

                this.state.data = {
                    ...defaults,
                    ...res,
                    kpis: { ...defaults.kpis, ...(res.kpis || {}) },
                    ai_kpis: { ...defaults.ai_kpis, ...(res.ai_kpis || {}) },
                    punctuality_pie: { ...defaults.punctuality_pie, ...(res.punctuality_pie || {}) },
                    charts: { ...defaults.charts, ...(res.charts || {}) },
                    tables: { ...defaults.tables, ...(res.tables || {}) },
                    leave_balances: { ...defaults.leave_balances, ...(res.leave_balances || {}) },
                    employee_profile: { ...defaults.employee_profile, ...(res.employee_profile || {}) },
                    career_path: { ...defaults.career_path, ...(res.career_path || {}) },
                    attendance_widget: {
                        ...defaults.attendance_widget,
                        ...(res.attendance_widget || {}),
                        summary: {
                            ...defaults.attendance_widget.summary,
                            ...((res.attendance_widget && res.attendance_widget.summary) || {})
                        },
                        calendar_days: safeCalendarDays
                    },
                    goals: res.goals || [],
                    trainings: res.trainings || [],
                    rewards: res.rewards || [],
                    warnings: res.warnings || [],
                    my_leaves: res.my_leaves || [],
                    pending_leave_approvals: res.pending_leave_approvals || [],
                    reports_data: res.reports_data || [],
                    nine_box: res.nine_box || [],
                    heatmap: res.heatmap || [],
                    recommendations: res.recommendations || [],
                };
            }
        } catch (err) {
            console.error("Dashboard RPC Error:", err);
        } finally {
            this.state.loading = false;
        }
    }

    openModelList(modelName, domain = [], title = "Records") {
        const safeDomain = Array.isArray(domain)
            ? domain.filter(item => Array.isArray(item) && item.length === 3 && item[2] !== undefined)
            : [];

        this.action.doAction({
            name: title,
            type: "ir.actions.act_window",
            res_model: modelName,
            views: [[false, "list"], [false, "form"]],
            domain: safeDomain,
            target: "current",
        });
    }

    openRecord(modelName, resId) {
        if (!resId) return;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: modelName,
            res_id: parseInt(resId),
            views: [[false, "form"]],
            target: "current",
        });
    }

    createNewRecord(modelName) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: modelName,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openActiveStaff() {
        this.openModelList('hr.employee', [['active', '=', true]], 'Active Staff');
    }

    openMyKpis() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        const domain = empId ? [['employee_id', '=', empId]] : [];
        this.openModelList('employee.kpi', domain, 'My KPIs');
    }

    openMyAttendance() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        const domain = empId ? [['employee_id', '=', empId]] : [];
        this.openModelList('employee.attendance.log', domain, 'My Attendance Logs');
    }

    openMyGoals() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        const domain = empId ? [['employee_id', '=', empId]] : [];
        this.openModelList('employee.goal', domain, 'My Goals');
    }

    openMyTrainings() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        const domain = empId ? [['employee_id', '=', empId]] : [];
        this.openModelList('training.enrollment', domain, 'My Trainings');
    }

    openMyRewards() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        const domain = empId ? [['employee_id', '=', empId]] : [];
        this.openModelList('reward.record', domain, 'My Rewards');
    }

    openMyWarnings() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        const domain = empId ? [['employee_id', '=', empId]] : [];
        this.openModelList('warning.record', domain, 'My Warnings');
    }

    async togglePunch() {
        try {
            await rpc("/smart_performance/attendance_punch", {
                employee_id: this.state.activeEmployeeId
            });
            await this.loadData(this.state.activeTab);
            this.notification.add("Punch status updated successfully!", { type: "success" });
        } catch (err) {
            console.error("Punch action error:", err);
            this.notification.add("Failed to record punch.", { type: "danger" });
        }
    }

    async submitLeaveApplication() {
        if (!this.state.leaveApplyForm.reason) {
            this.notification.add("Please provide a reason for your leave request.", { type: "warning" });
            return;
        }
        try {
            const res = await rpc("/smart_performance/submit_leave", {
                vals: {
                    employee_id: this.state.activeEmployeeId,
                    leave_type: this.state.leaveApplyForm.leave_type,
                    date_from: this.state.leaveApplyForm.date_from,
                    date_to: this.state.leaveApplyForm.date_to,
                    reason: this.state.leaveApplyForm.reason
                }
            });
            if (res && res.status === 'success') {
                this.notification.add(`Leave Application (${res.reference}) submitted!`, { type: "success" });
                this.state.leaveApplyForm.reason = "";
                await this.loadData(this.state.activeTab);
            }
        } catch (err) {
            this.notification.add(err.message || "Failed to submit leave application.", { type: "danger" });
        }
    }

    async handleLeaveDecision(leaveId, decision) {
        try {
            const res = await rpc("/smart_performance/process_leave_decision", {
                leave_id: leaveId,
                decision: decision,
                current_role: this.state.activeRole
            });
            if (res && res.status === 'success') {
                this.notification.add(`Leave Request has been ${decision.toUpperCase()}ED.`, { type: "success" });
                await this.loadData(this.state.activeTab);
            } else {
                this.notification.add((res && res.message) || "Hierarchy violation in leave approval.", { type: "danger" });
            }
        } catch (err) {
            this.notification.add("Failed to process leave approval decision.", { type: "danger" });
        }
    }

    async prevMonth() {
        if (this.state.calMonth === 1) {
            this.state.calMonth = 12;
            this.state.calYear -= 1;
        } else {
            this.state.calMonth -= 1;
        }
        await this.loadData(this.state.activeTab);
    }

    async nextMonth() {
        if (this.state.calMonth === 12) {
            this.state.calMonth = 1;
            this.state.calYear += 1;
        } else {
            this.state.calMonth += 1;
        }
        await this.loadData(this.state.activeTab);
    }

    downloadXLSX() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        window.location.href = empId ? `/smart_performance/export_kpi_xlsx?employee_id=${encodeURIComponent(empId)}` : "/smart_performance/export_kpi_xlsx";
    }

    downloadCSV() {
        const empId = this.state.activeEmployeeId || (this.state.data.employee_profile && this.state.data.employee_profile.id);
        window.location.href = empId ? `/smart_performance/export_kpi_csv?employee_id=${encodeURIComponent(empId)}` : "/smart_performance/export_kpi_csv";
    }
}

registry.category("actions").add("action_open_performance_dashboard", SmartPerformanceDashboard);
registry.category("actions").add("smart_performance_dashboard", SmartPerformanceDashboard);