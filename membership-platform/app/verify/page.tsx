"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Shield, CheckCircle, FileText, User } from "lucide-react"

export default function VerifyPage() {
  const [user, setUser] = useState<any>(null)
  const [documentType, setDocumentType] = useState("")
  const [documentNumber, setDocumentNumber] = useState("")
  const [loading, setLoading] = useState(false)
  const [verificationStep, setVerificationStep] = useState(1)
  const [verificationData, setVerificationData] = useState<any>(null)
  const [error, setError] = useState("")
  const router = useRouter()

  useEffect(() => {
    const userData = localStorage.getItem("user")
    if (userData) {
      setUser(JSON.parse(userData))
    } else {
      router.push("/login")
    }
  }, [router])

  const handleDocumentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    // Simulate DigiLocker API call
    setTimeout(() => {
      const mockData = {
        aadhaar_number: documentType === "aadhaar" ? documentNumber : null,
        voter_id: documentType === "voter_id" ? documentNumber : null,
        name: "John Doe",
        dob: "1990-05-15",
        gender: "Male",
        address: "123 Main Street, City, State 12345",
        document_type: documentType,
        photo: "/placeholder.svg?height=150&width=150",
      }

      setVerificationData(mockData)
      setVerificationStep(2)
      setLoading(false)
    }, 2000)
  }

  const handleVerificationConfirm = async () => {
    setLoading(true)

    try {
      const response = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: user.id,
          ...verificationData,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setVerificationStep(3)
        setTimeout(() => {
          router.push("/dashboard")
        }, 2000)
      } else {
        setError(data.error || "Verification failed")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="container mx-auto max-w-2xl">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Shield className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold">MembershipPro</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Identity Verification</h1>
          <p className="text-gray-600">Secure your account with DigiLocker verification</p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 ${verificationStep >= 1 ? "text-blue-600" : "text-gray-400"}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${verificationStep >= 1 ? "bg-blue-600 text-white" : "bg-gray-200"}`}
              >
                1
              </div>
              <span>Document</span>
            </div>
            <div className="w-8 h-px bg-gray-300"></div>
            <div className={`flex items-center space-x-2 ${verificationStep >= 2 ? "text-blue-600" : "text-gray-400"}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${verificationStep >= 2 ? "bg-blue-600 text-white" : "bg-gray-200"}`}
              >
                2
              </div>
              <span>Verify</span>
            </div>
            <div className="w-8 h-px bg-gray-300"></div>
            <div
              className={`flex items-center space-x-2 ${verificationStep >= 3 ? "text-green-600" : "text-gray-400"}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${verificationStep >= 3 ? "bg-green-600 text-white" : "bg-gray-200"}`}
              >
                {verificationStep >= 3 ? <CheckCircle className="h-4 w-4" /> : "3"}
              </div>
              <span>Complete</span>
            </div>
          </div>
        </div>

        {verificationStep === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Select Document Type</span>
              </CardTitle>
              <CardDescription>Choose your government-issued document for verification</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleDocumentSubmit} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label>Document Type</Label>
                  <Select value={documentType} onValueChange={setDocumentType} required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select document type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="aadhaar">Aadhaar Card</SelectItem>
                      <SelectItem value="voter_id">Voter ID</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="documentNumber">
                    {documentType === "aadhaar" ? "Aadhaar Number" : "Voter ID Number"}
                  </Label>
                  <Input
                    id="documentNumber"
                    value={documentNumber}
                    onChange={(e) => setDocumentNumber(e.target.value)}
                    placeholder={documentType === "aadhaar" ? "1234-5678-9012" : "ABC1234567"}
                    required
                  />
                </div>

                <Button type="submit" className="w-full" disabled={loading || !documentType}>
                  {loading ? "Connecting to DigiLocker..." : "Verify with DigiLocker"}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {verificationStep === 2 && verificationData && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Confirm Your Details</span>
              </CardTitle>
              <CardDescription>Please verify the information retrieved from DigiLocker</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center space-x-4">
                <img
                  src={verificationData.photo || "/placeholder.svg"}
                  alt="Profile"
                  className="w-24 h-24 rounded-lg object-cover border"
                />
                <div>
                  <Badge variant="secondary" className="mb-2">
                    {verificationData.document_type === "aadhaar" ? "Aadhaar Verified" : "Voter ID Verified"}
                  </Badge>
                  <h3 className="text-xl font-semibold">{verificationData.name}</h3>
                  <p className="text-gray-600">DOB: {verificationData.dob}</p>
                  <p className="text-gray-600">Gender: {verificationData.gender}</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Address</Label>
                <p className="p-3 bg-gray-50 rounded-lg text-sm">{verificationData.address}</p>
              </div>

              <div className="space-y-2">
                <Label>Document Number</Label>
                <p className="p-3 bg-gray-50 rounded-lg text-sm font-mono">
                  {verificationData.aadhaar_number || verificationData.voter_id}
                </p>
              </div>

              <div className="flex space-x-4">
                <Button onClick={() => setVerificationStep(1)} variant="outline" className="flex-1">
                  Back
                </Button>
                <Button onClick={handleVerificationConfirm} className="flex-1" disabled={loading}>
                  {loading ? "Confirming..." : "Confirm & Complete"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {verificationStep === 3 && (
          <Card>
            <CardContent className="text-center py-8">
              <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-green-600 mb-2">Verification Complete!</h2>
              <p className="text-gray-600 mb-4">
                Your identity has been successfully verified. You now have full access to the platform.
              </p>
              <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
