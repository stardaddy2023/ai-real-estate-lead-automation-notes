"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { Settings, Key, Globe, Database, Shield, Check, X, RefreshCw, Eye, EyeOff, Save } from "lucide-react"

interface SettingItem {
    key: string
    masked_value: string
    description: string
    category: string
    is_configured: boolean
    updated_at: string | null
}

interface TestResult {
    key: string
    success: boolean
    message: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function SettingsPage() {
    const [settings, setSettings] = useState<SettingItem[]>([])
    const [loading, setLoading] = useState(true)
    const [editValues, setEditValues] = useState<Record<string, string>>({})
    const [showValues, setShowValues] = useState<Record<string, boolean>>({})
    const [testing, setTesting] = useState<Record<string, boolean>>({})
    const [testResults, setTestResults] = useState<Record<string, TestResult>>({})
    const [saving, setSaving] = useState<Record<string, boolean>>({})
    // Custom setting creation state
    const [showAddForm, setShowAddForm] = useState(false)
    const [newKey, setNewKey] = useState("")
    const [newValue, setNewValue] = useState("")
    const [newDescription, setNewDescription] = useState("")
    const [newCategory, setNewCategory] = useState("custom")
    const [creating, setCreating] = useState(false)
    // Admin authentication state
    const [adminKey, setAdminKey] = useState("")
    const [showAdminPrompt, setShowAdminPrompt] = useState(false)
    const [adminKeyInput, setAdminKeyInput] = useState("")
    const { toast } = useToast()

    // Load admin key from sessionStorage on mount
    useEffect(() => {
        const storedKey = sessionStorage.getItem("arela_admin_key")
        if (storedKey) {
            setAdminKey(storedKey)
        }
    }, [])

    // Fetch settings on mount
    useEffect(() => {
        fetchSettings()
    }, [])

    const fetchSettings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/settings`)
            if (res.ok) {
                const data = await res.json()
                setSettings(data)
            }
        } catch (error) {
            console.error("Failed to fetch settings:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async (key: string) => {
        const value = editValues[key]
        if (!value) return

        setSaving(prev => ({ ...prev, [key]: true }))
        try {
            const headers: Record<string, string> = { "Content-Type": "application/json" }
            if (adminKey) {
                headers["X-Admin-Key"] = adminKey
            }

            const res = await fetch(`${API_BASE}/api/v1/settings/${key}`, {
                method: "PUT",
                headers,
                body: JSON.stringify({ value })
            })

            if (res.ok) {
                toast({
                    title: "Saved",
                    description: `${key} has been updated.`,
                })
                // Clear edit value and refresh
                setEditValues(prev => ({ ...prev, [key]: "" }))
                fetchSettings()
            } else if (res.status === 401) {
                // Need admin authentication
                setShowAdminPrompt(true)
                toast({
                    title: "Authentication Required",
                    description: "Please enter admin key to modify settings.",
                    variant: "destructive"
                })
            } else {
                toast({
                    title: "Error",
                    description: "Failed to save setting.",
                    variant: "destructive"
                })
            }
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to save setting.",
                variant: "destructive"
            })
        } finally {
            setSaving(prev => ({ ...prev, [key]: false }))
        }
    }

    const handleTest = async (key: string) => {
        setTesting(prev => ({ ...prev, [key]: true }))
        setTestResults(prev => {
            const newResults = { ...prev }
            delete newResults[key]
            return newResults
        })

        try {
            const res = await fetch(`${API_BASE}/api/v1/settings/${key}/test`, {
                method: "POST"
            })

            if (res.ok) {
                const result: TestResult = await res.json()
                setTestResults(prev => ({ ...prev, [key]: result }))

                toast({
                    title: result.success ? "Test Passed" : "Test Failed",
                    description: result.message,
                    variant: result.success ? "default" : "destructive"
                })
            }
        } catch (error) {
            setTestResults(prev => ({
                ...prev,
                [key]: { key, success: false, message: "Test request failed" }
            }))
        } finally {
            setTesting(prev => ({ ...prev, [key]: false }))
        }
    }

    const toggleShowValue = (key: string) => {
        setShowValues(prev => ({ ...prev, [key]: !prev[key] }))
    }

    const handleCreateSetting = async () => {
        if (!newKey.trim() || !newValue.trim()) {
            toast({
                title: "Error",
                description: "Key and Value are required",
                variant: "destructive"
            })
            return
        }

        setCreating(true)
        try {
            const headers: Record<string, string> = { "Content-Type": "application/json" }
            if (adminKey) {
                headers["X-Admin-Key"] = adminKey
            }

            const res = await fetch(`${API_BASE}/api/v1/settings`, {
                method: "POST",
                headers,
                body: JSON.stringify({
                    key: newKey.toUpperCase().replace(/\s+/g, "_"),
                    value: newValue,
                    description: newDescription || `Custom setting: ${newKey}`,
                    category: newCategory,
                })
            })

            if (res.ok) {
                toast({
                    title: "Created",
                    description: `Setting ${newKey} has been created.`,
                })
                // Reset form
                setNewKey("")
                setNewValue("")
                setNewDescription("")
                setNewCategory("custom")
                setShowAddForm(false)
                fetchSettings()
            } else if (res.status === 401) {
                // Need admin authentication
                setShowAdminPrompt(true)
                toast({
                    title: "Authentication Required",
                    description: "Please enter admin key to create settings.",
                    variant: "destructive"
                })
            } else {
                const data = await res.json()
                toast({
                    title: "Error",
                    description: data.detail || "Failed to create setting.",
                    variant: "destructive"
                })
            }
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to create setting.",
                variant: "destructive"
            })
        } finally {
            setCreating(false)
        }
    }

    const handleUnlock = () => {
        if (adminKeyInput.trim()) {
            setAdminKey(adminKeyInput)
            sessionStorage.setItem("arela_admin_key", adminKeyInput)
            setShowAdminPrompt(false)
            setAdminKeyInput("")
            toast({
                title: "Unlocked",
                description: "Admin access enabled for this session.",
            })
        }
    }

    if (loading) {
        return (
            <div className="p-8 h-full flex items-center justify-center">
                <RefreshCw className="h-8 w-8 animate-spin text-gray-500" />
            </div>
        )
    }

    const apiKeySettings = settings.filter(s => s.category === "api_keys")

    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Settings className="h-8 w-8 text-primary" />
                        <div>
                            <h1 className="text-3xl font-bold text-white">Settings</h1>
                            <p className="text-gray-400">Configure API keys and integrations</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {adminKey ? (
                            <Badge className="bg-green-600 text-white">
                                <Shield className="h-3 w-3 mr-1" />
                                Admin
                            </Badge>
                        ) : (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setShowAdminPrompt(true)}
                                className="border-yellow-500 text-yellow-500 hover:bg-yellow-500/10"
                            >
                                <Shield className="h-4 w-4 mr-1" />
                                Unlock
                            </Button>
                        )}
                        <Button
                            onClick={() => setShowAddForm(!showAddForm)}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            {showAddForm ? "Cancel" : "+ Add Custom"}
                        </Button>
                    </div>
                </div>

                {/* Admin Unlock Prompt */}
                {showAdminPrompt && (
                    <Card className="bg-gray-900/50 border-yellow-500/50 border-2">
                        <CardHeader>
                            <CardTitle className="text-white flex items-center gap-2">
                                <Shield className="h-5 w-5 text-yellow-400" />
                                Admin Authentication Required
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-gray-400">Enter your admin key to modify settings:</p>
                            <div className="flex gap-2">
                                <Input
                                    type="password"
                                    placeholder="Enter admin key..."
                                    value={adminKeyInput}
                                    onChange={(e) => setAdminKeyInput(e.target.value)}
                                    className="bg-gray-900 border-gray-700 text-white flex-1"
                                    onKeyDown={(e) => e.key === 'Enter' && handleUnlock()}
                                />
                                <Button onClick={handleUnlock} className="bg-yellow-600 hover:bg-yellow-700">
                                    Unlock
                                </Button>
                                <Button variant="outline" onClick={() => setShowAdminPrompt(false)}>
                                    Cancel
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Add Custom Form */}
                {showAddForm && (
                    <Card className="bg-gray-900/50 border-blue-500/50 border-2">
                        <CardHeader>
                            <CardTitle className="text-white">Add Custom Setting</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-gray-400 mb-1 block">Key Name *</label>
                                    <Input
                                        placeholder="e.g., MY_API_KEY"
                                        value={newKey}
                                        onChange={(e) => setNewKey(e.target.value)}
                                        className="bg-gray-900 border-gray-700 text-white"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 mb-1 block">Value *</label>
                                    <Input
                                        type="password"
                                        placeholder="Enter value..."
                                        value={newValue}
                                        onChange={(e) => setNewValue(e.target.value)}
                                        className="bg-gray-900 border-gray-700 text-white"
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-gray-400 mb-1 block">Description</label>
                                    <Input
                                        placeholder="What is this setting for?"
                                        value={newDescription}
                                        onChange={(e) => setNewDescription(e.target.value)}
                                        className="bg-gray-900 border-gray-700 text-white"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 mb-1 block">Category</label>
                                    <select
                                        value={newCategory}
                                        onChange={(e) => setNewCategory(e.target.value)}
                                        className="w-full h-10 px-3 bg-gray-900 border border-gray-700 rounded-md text-white"
                                    >
                                        <option value="api_keys">API Keys</option>
                                        <option value="integrations">Integrations</option>
                                        <option value="custom">Custom</option>
                                    </select>
                                </div>
                            </div>
                            <Button
                                onClick={handleCreateSetting}
                                disabled={creating || !newKey.trim() || !newValue.trim()}
                                className="bg-green-600 hover:bg-green-700"
                            >
                                {creating ? (
                                    <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                                ) : null}
                                Create Setting
                            </Button>
                        </CardContent>
                    </Card>
                )}

                {/* API Keys Section */}
                <Card className="bg-gray-900/50 border-gray-800">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <Key className="h-5 w-5 text-yellow-400" />
                            API Keys
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {apiKeySettings.map((setting) => (
                            <div
                                key={setting.key}
                                className="p-4 bg-gray-800/50 rounded-lg border border-gray-700 space-y-3"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-medium text-white">{setting.key}</h3>
                                        <p className="text-sm text-gray-400">{setting.description}</p>
                                    </div>
                                    <Badge
                                        className={setting.is_configured
                                            ? "bg-green-500/20 text-green-400 border-green-500/50"
                                            : "bg-gray-500/20 text-gray-400 border-gray-500/50"
                                        }
                                    >
                                        {setting.is_configured ? "Configured" : "Not Configured"}
                                    </Badge>
                                </div>

                                {/* Current Value Display */}
                                {setting.is_configured && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <span className="text-gray-500">Current:</span>
                                        <code className="px-2 py-1 bg-gray-900 rounded text-gray-300">
                                            {setting.masked_value}
                                        </code>
                                        {setting.updated_at && (
                                            <span className="text-gray-500 text-xs">
                                                Updated: {new Date(setting.updated_at).toLocaleDateString()}
                                            </span>
                                        )}
                                    </div>
                                )}

                                {/* Input and Actions */}
                                <div className="flex gap-2">
                                    <div className="relative flex-1">
                                        <Input
                                            type={showValues[setting.key] ? "text" : "password"}
                                            placeholder="Enter new API key..."
                                            value={editValues[setting.key] || ""}
                                            onChange={(e) => setEditValues(prev => ({
                                                ...prev,
                                                [setting.key]: e.target.value
                                            }))}
                                            className="bg-gray-900 border-gray-700 text-white pr-10"
                                        />
                                        <button
                                            onClick={() => toggleShowValue(setting.key)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                                        >
                                            {showValues[setting.key] ? (
                                                <EyeOff className="h-4 w-4" />
                                            ) : (
                                                <Eye className="h-4 w-4" />
                                            )}
                                        </button>
                                    </div>
                                    <Button
                                        onClick={() => handleSave(setting.key)}
                                        disabled={!editValues[setting.key] || saving[setting.key]}
                                        className="bg-green-600 hover:bg-green-700"
                                    >
                                        {saving[setting.key] ? (
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Save className="h-4 w-4" />
                                        )}
                                    </Button>
                                    <Button
                                        variant="outline"
                                        onClick={() => handleTest(setting.key)}
                                        disabled={!setting.is_configured || testing[setting.key]}
                                        className="border-gray-600"
                                    >
                                        {testing[setting.key] ? (
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                        ) : (
                                            "Test"
                                        )}
                                    </Button>
                                </div>

                                {/* Test Result */}
                                {testResults[setting.key] && (
                                    <div className={`flex items-center gap-2 text-sm p-2 rounded ${testResults[setting.key].success
                                        ? "bg-green-900/20 text-green-400"
                                        : "bg-red-900/20 text-red-400"
                                        }`}>
                                        {testResults[setting.key].success ? (
                                            <Check className="h-4 w-4" />
                                        ) : (
                                            <X className="h-4 w-4" />
                                        )}
                                        {testResults[setting.key].message}
                                    </div>
                                )}
                            </div>
                        ))}
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
                        {settings.filter(s => s.category === "integrations").map((setting) => (
                            <div
                                key={setting.key}
                                className="p-4 bg-gray-800/50 rounded-lg border border-gray-700 space-y-3"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-medium text-white">{setting.key}</h3>
                                        <p className="text-sm text-gray-400">{setting.description}</p>
                                    </div>
                                    <Badge
                                        className={setting.is_configured
                                            ? "bg-green-500/20 text-green-400 border-green-500/50"
                                            : "bg-gray-500/20 text-gray-400 border-gray-500/50"
                                        }
                                    >
                                        {setting.is_configured ? "Configured" : "Not Configured"}
                                    </Badge>
                                </div>

                                {/* Current Value Display */}
                                {setting.is_configured && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <span className="text-gray-500">Current:</span>
                                        <code className="px-2 py-1 bg-gray-900 rounded text-gray-300">
                                            {setting.masked_value}
                                        </code>
                                    </div>
                                )}

                                {/* Input and Actions */}
                                <div className="flex gap-2">
                                    <Input
                                        type="text"
                                        placeholder="Enter value..."
                                        value={editValues[setting.key] || ""}
                                        onChange={(e) => setEditValues(prev => ({
                                            ...prev,
                                            [setting.key]: e.target.value
                                        }))}
                                        className="bg-gray-900 border-gray-700 text-white flex-1"
                                    />
                                    <Button
                                        onClick={() => handleSave(setting.key)}
                                        disabled={!editValues[setting.key] || saving[setting.key]}
                                        className="bg-green-600 hover:bg-green-700"
                                    >
                                        {saving[setting.key] ? (
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Save className="h-4 w-4" />
                                        )}
                                    </Button>
                                </div>
                            </div>
                        ))}
                        {settings.filter(s => s.category === "integrations").length === 0 && (
                            <div className="p-4 border border-dashed border-gray-700 rounded-lg text-center">
                                <Database className="h-8 w-8 mx-auto mb-2 text-gray-500" />
                                <p className="text-gray-400">No integration settings available.</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
