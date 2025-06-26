import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest, { params }: { params: { userId: string } }) {
  try {
    const userId = Number.parseInt(params.userId)

    // Mock verification data
    const mockVerifications = [
      {
        id: 1,
        user_id: 2,
        aadhaar_number: "1234-5678-9012",
        name: "John Doe",
        dob: "1990-05-15",
        gender: "Male",
        address: "123 Main St, City, State 12345",
        document_type: "aadhaar",
        verified_at: "2024-01-15T10:00:00Z",
      },
      {
        id: 2,
        user_id: 3,
        aadhaar_number: "9876-5432-1098",
        name: "Jane Smith",
        dob: "1985-08-22",
        gender: "Female",
        address: "456 Oak Ave, Town, State 67890",
        document_type: "aadhaar",
        verified_at: "2024-01-20T14:30:00Z",
      },
    ]

    const verification = mockVerifications.find((v) => v.user_id === userId)

    if (!verification) {
      return NextResponse.json({ error: "Verification not found" }, { status: 404 })
    }

    return NextResponse.json(verification)
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
