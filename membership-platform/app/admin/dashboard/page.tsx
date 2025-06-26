"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Shield, Users, Calendar, Plus, LogOut, Edit, Trash2 } from "lucide-react"

export default function AdminDashboardPage() {
  const [user, setUser] = useState<any>(null)
  const [events, setEvents] = useState<any[]>([])
  const [members, setMembers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isAddingEvent, setIsAddingEvent] = useState(false)
  const [newEvent, setNewEvent] = useState({
    title: "",
    description: "",
    start_time: "",
    end_time: "",
  })
  const router = useRouter()

  useEffect(() => {
    const userData = localStorage.getItem("user")
    if (userData) {
      const parsedUser = JSON.parse(userData)
      if (!parsedUser.is_admin) {
        router.push("/dashboard")
        return
      }
      setUser(parsedUser)
      fetchAdminData()
    } else {
      router.push("/login")
    }
  }, [router])

  const fetchAdminData = async () => {
    try {
      const [eventsRes, membersRes] = await Promise.all([fetch("/api/events"), fetch("/api/admin/members")])

      if (eventsRes.ok) {
        const eventsData = await eventsRes.json()
        setEvents(eventsData)
      }

      if (membersRes.ok) {
        const membersData = await membersRes.json()
        setMembers(membersData)
      }
    } catch (error) {
      console.error("Error fetching admin data:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddEvent = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsAddingEvent(true)

    try {
      const response = await fetch("/api/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newEvent,
          admin_id: user.id,
        }),
      })

      if (response.ok) {
        const eventData = await response.json()
        setEvents([eventData, ...events])
        setNewEvent({ title: "", description: "", start_time: "", end_time: "" })
        setIsAddingEvent(false)
      }
    } catch (error) {
      console.error("Error adding event:", error)
    } finally {
      setIsAddingEvent(false)
    }
  }

  const handleDeleteEvent = async (eventId: number) => {
    try {
      const response = await fetch(`/api/events/${eventId}`, {
        method: "DELETE",
      })

      if (response.ok) {
        setEvents(events.filter((event) => event.id !== eventId))
      }
    } catch (error) {
      console.error("Error deleting event:", error)
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
            <Badge className="bg-red-100 text-red-800">Admin</Badge>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Admin: {user.email}</span>
            <Button onClick={handleLogout} variant="outline" size="sm">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Members</p>
                  <p className="text-3xl font-bold">{members.length}</p>
                </div>
                <Users className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Verified Members</p>
                  <p className="text-3xl font-bold">{members.filter((m) => m.verification_status).length}</p>
                </div>
                <Shield className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Events</p>
                  <p className="text-3xl font-bold">{events.length}</p>
                </div>
                <Calendar className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Events Management */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Event Management</CardTitle>
                  <CardDescription>Create and manage platform events</CardDescription>
                </div>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Event
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create New Event</DialogTitle>
                      <DialogDescription>Add a new event for platform members</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleAddEvent} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="title">Event Title</Label>
                        <Input
                          id="title"
                          value={newEvent.title}
                          onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                          placeholder="Enter event title"
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="description">Description</Label>
                        <Textarea
                          id="description"
                          value={newEvent.description}
                          onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                          placeholder="Enter event description"
                          rows={3}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="start_time">Start Time</Label>
                          <Input
                            id="start_time"
                            type="datetime-local"
                            value={newEvent.start_time}
                            onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="end_time">End Time</Label>
                          <Input
                            id="end_time"
                            type="datetime-local"
                            value={newEvent.end_time}
                            onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}
                            required
                          />
                        </div>
                      </div>

                      <Button type="submit" className="w-full" disabled={isAddingEvent}>
                        {isAddingEvent ? "Creating..." : "Create Event"}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {events.map((event) => (
                  <div key={event.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">{event.title}</h3>
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleDeleteEvent(event.id)}>
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm mb-2">{event.description}</p>
                    <div className="flex justify-between items-center text-sm text-gray-500">
                      <span>{new Date(event.start_time).toLocaleDateString()}</span>
                      <Badge variant="outline">
                        {new Date(event.start_time).toLocaleTimeString()} -{" "}
                        {new Date(event.end_time).toLocaleTimeString()}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Members Management */}
          <Card>
            <CardHeader>
              <CardTitle>Member Management</CardTitle>
              <CardDescription>View and manage platform members</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {members.map((member) => (
                  <div key={member.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold">{member.email}</h3>
                        {member.name && <p className="text-sm text-gray-600">{member.name}</p>}
                      </div>
                      <div className="flex flex-col items-end space-y-1">
                        <Badge variant={member.verification_status ? "default" : "secondary"}>
                          {member.verification_status ? "Verified" : "Unverified"}
                        </Badge>
                        {member.is_admin && <Badge className="bg-red-100 text-red-800">Admin</Badge>}
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      <p>Joined: {new Date(member.created_at).toLocaleDateString()}</p>
                      {member.verification_status && member.verified_at && (
                        <p>Verified: {new Date(member.verified_at).toLocaleDateString()}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
