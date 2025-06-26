import { type NextRequest, NextResponse } from "next/server"

const mockEvents = [
  {
    id: 1,
    admin_id: 1,
    title: "Annual General Meeting",
    description: "Annual meeting for all members to discuss platform updates and future plans.",
    start_time: "2024-02-15T10:00:00Z",
    end_time: "2024-02-15T12:00:00Z",
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    admin_id: 1,
    title: "Tech Workshop",
    description: "Workshop on latest technology trends and digital literacy.",
    start_time: "2024-02-20T14:00:00Z",
    end_time: "2024-02-20T17:00:00Z",
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 3,
    admin_id: 1,
    title: "Community Outreach",
    description: "Community service event for verified members.",
    start_time: "2024-02-25T09:00:00Z",
    end_time: "2024-02-25T16:00:00Z",
    created_at: "2024-01-01T00:00:00Z",
  },
]

export async function GET() {
  try {
    return NextResponse.json(mockEvents)
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const eventData = await request.json()

    const newEvent = {
      id: Math.floor(Math.random() * 1000) + 100,
      ...eventData,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    mockEvents.unshift(newEvent)
    return NextResponse.json(newEvent)
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
