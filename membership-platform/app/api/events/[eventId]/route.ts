import { type NextRequest, NextResponse } from "next/server"

export async function DELETE(request: NextRequest, { params }: { params: { eventId: string } }) {
  try {
    const eventId = Number.parseInt(params.eventId)

    // Mock deletion (in real app, delete from database)
    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
