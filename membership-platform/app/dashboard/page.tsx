"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Shield, User, Calendar, CheckCircle, LogOut, FileText } from "lucide-react"

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null)
  const [verification, setVerification] = useState<any>(null)
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const userData = localStorage.getItem("user")
    if (userData) {
      const parsedUser = JSON.parse(userData)
      setUser(parsedUser)
      fetchUserData(parsedUser.id)
    } else {
      router.push("/login")
    }
  }, [router])

  const fetchUserData = async (userId: number) => {
    try {
      const [verificationRes, eventsRes] = await Promise.all([
        fetch(`/api/verification/${userId}`),
        fetch("/api/events"),
      ])

      if (verificationRes.ok) {
        const verificationData = await verificationRes.json()
        setVerification(verificationData)
      }

      if (eventsRes.ok) {
        const eventsData = await eventsRes.json()
        setEvents(eventsData)
      }
    } catch (error) {
      console.error("Error fetching user data:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("user")
    router.push("/")
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold">MembershipPro</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Welcome, {user.email}</span>
            <Button onClick={handleLogout} variant="outline" size="sm">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Verification Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5" />
                  <span>Verification Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {verification ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Identity Verification</span>
                      <Badge className="bg-green-100 text-green-800">Verified</Badge>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4 p-4 bg-green-50 rounded-lg">
                      <div>
                        <p className="text-sm text-gray-600">Name</p>
                        <p className="font-semibold">{verification.name}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Document Type</p>
                        <p className="font-semibold capitalize">{verification.document_type}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Date of Birth</p>
                        <p className="font-semibold">{verification.dob}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Verified On</p>
                        <p className="font-semibold">{new Date(verification.verified_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-4">Identity verification pending</p>
                    <Button onClick={() => router.push("/verify")}>Complete Verification</Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Upcoming Events */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5" />
                  <span>Upcoming Events</span>
                </CardTitle>
                <CardDescription>Events you can participate in</CardDescription>
              </CardHeader>
              <CardContent>
                {events.length > 0 ? (
                  <div className="space-y-4">
                    {events.map((event) => (
                      <div key={event.id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-semibold">{event.title}</h3>
                          <Badge variant="outline">{new Date(event.start_time).toLocaleDateString()}</Badge>
                        </div>
                        <p className="text-gray-600 text-sm mb-2">{event.description}</p>
                        <div className="flex justify-between items-center text-sm text-gray-500">
                          <span>
                            {new Date(event.start_time).toLocaleTimeString()} -{" "}
                            {new Date(event.end_time).toLocaleTimeString()}
                          </span>
                          {verification && <Badge className="bg-blue-100 text-blue-800">Eligible</Badge>}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 text-center py-8">No upcoming events</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Profile Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <User className="h-5 w-5" />
                  <span>Profile</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600">Email</p>
                  <p className="font-semibold">{user.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Member Since</p>
                  <p className="font-semibold">{new Date(user.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Account Type</p>
                  <Badge variant={user.is_admin ? "default" : "secondary"}>{user.is_admin ? "Admin" : "Member"}</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {!verification && (
                  <Button onClick={() => router.push("/verify")} className="w-full" variant="outline">
                    Complete Verification
                  </Button>
                )}
                <Button onClick={() => window.location.reload()} className="w-full" variant="outline">
                  Refresh Data
                </Button>
              </CardContent>
            </Card>

            {/* Membership Info */}
            {verification && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  Your membership is active and verified. You have access to all platform features.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
