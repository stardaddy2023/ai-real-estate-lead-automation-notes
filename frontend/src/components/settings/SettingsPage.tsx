"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Settings, Key, Globe, Database, Shield } from "lucide-react"

export function SettingsPage() {
    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-3">
                    <Settings className="h-8 w-8 text-primary" />
                    <div>
                        <h1 className="text-3xl font-bold text-white">Settings</h1>
                        <p className="text-gray-400">Configure API keys and integrations</p>
                    </div>
                </div>

                {/* API Keys Section */}
                <Card className="bg-gray-900/50 border-gray-800">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <Key className="h-5 w-5 text-yellow-400" />
                            API Keys
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="p-4 border border-dashed border-gray-700 rounded-lg text-center">
                            <Shield className="h-8 w-8 mx-auto mb-2 text-gray-500" />
                            <p className="text-gray-400">API key configuration coming soon.</p>
                            <p className="text-xs text-gray-500 mt-1">Google Maps, County Assessors, FRED, Census, BLS</p>
                        </div>
                    </CardContent>
                </Card>

                {/* Integrations Section */}
                <Card className="bg-gray-900/50 border-gray-800">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <Globe className="h-5 w-5 text-blue-400" />
                            Integrations
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="p-4 border border-dashed border-gray-700 rounded-lg text-center">
                            <Database className="h-8 w-8 mx-auto mb-2 text-gray-500" />
                            <p className="text-gray-400">MCP server and data source configuration coming soon.</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
