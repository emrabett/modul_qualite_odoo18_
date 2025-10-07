/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class QualityDashboard extends Component {
    setup() {
        this.state = useState({
            metrics: {},
            loading: true,
            error: null
        });
        
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        onMounted(() => {
            this.loadDashboardData();
        });
    }
    
    async loadDashboardData() {
        try {
            this.state.loading = true;
            const data = await this.orm.call(
                'quality.plan',
                'get_dashboard_data',
                []
            );
            this.state.metrics = data;
            this.state.loading = false;
        } catch (error) {
            console.error('Erreur lors du chargement du dashboard:', error);
            this.state.error = error.message;
            this.state.loading = false;
            this.notification.add(
                "Erreur lors du chargement du dashboard",
                { type: "danger" }
            );
        }
    }
    
    async refreshDashboard() {
        await this.loadDashboardData();
    }
}

QualityDashboard.template = 'quality_management.dashboard';
QualityDashboard.props = {};

registry.category("actions").add("quality_dashboard", QualityDashboard);
