import { NextResponse } from "next/server"

export async function GET() {
  try {
    // Mock members data with verification status
    const mockMembers = [
      {
        id: 1,
        email: "admin@example.com",
        is_admin: true,
        created_at: "2024-01-01T00:00:00Z",
        verification_status: true,
        name: "Admin User",
        verified_at: "2024-01-01T00:00:00Z",
      },
      {
        id: 2,
        email: "user@example.com",
        is_admin: false,
        created_at: "2024-01-15T00:00:00Z",
        verification_status: true,
        name: "John Doe",
        verified_at: "2024-01-15T10:00:00Z",
      },
      {
        id: 3,
        email: "john.doe@example.com",
        is_admin: false,
        created_at: "2024-01-20T00:00:00Z",
        verification_status: true,
        name: "Jane Smith",
        verified_at: "2024-01-20T14:30:00Z",
      },
      {
        id: 4,
        email: "newuser@example.com",
        is_admin: false,
        created_at: "2024-01-25T00:00:00Z",
        verification_status: false,
        name: null,
        verified_at: null,
      },
    ]

    return NextResponse.json(mockMembers)
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
