"use client"

import type React from "react"

import { useState, useRef, useCallback, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Upload, Crop, MousePointer, X, Square, Beer as Blur, Download, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"

type Tool = "select" | "deselect" | "crop" | "blackout" | "blur"

interface Selection {
  x: number
  y: number
  width: number
  height: number
}

export function InvestigatorTool() {
  const [selectedTool, setSelectedTool] = useState<Tool>("select")
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [selections, setSelections] = useState<Selection[]>([])
  const [isDrawing, setIsDrawing] = useState(false)
  const [currentSelection, setCurrentSelection] = useState<Selection | null>(null)
  const [processedImage, setProcessedImage] = useState<string | null>(null)
  const [naturalSize, setNaturalSize] = useState<{ width: number; height: number } | null>(null)

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

  const tools = [
    { id: "select" as Tool, name: "Select Tool", icon: MousePointer, description: "Click to select an object" },
    { id: "deselect" as Tool, name: "Deselect Tool", icon: X, description: "Remove objects from selection" },
    { id: "crop" as Tool, name: "Crop Tool", icon: Crop, description: "Crop parts of an image" },
    { id: "blackout" as Tool, name: "Blackout Tool", icon: Square, description: "Cover selected parts in black" },
    { id: "blur" as Tool, name: "Blur Tool", icon: Blur, description: "Blur selected parts" },
  ]

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setUploadedImage(e.target?.result as string)
        setSelections([])
        setProcessedImage(null)
      }
      reader.readAsDataURL(file)
    }
  }, [])

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext("2d")
    const img = imageRef.current

    if (!canvas || !ctx || !img || !uploadedImage) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw image
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

    // Draw selections
    ctx.strokeStyle = "#6366f1"
    ctx.lineWidth = 2
    ctx.setLineDash([5, 5])

    selections.forEach((selection) => {
      ctx.strokeRect(selection.x, selection.y, selection.width, selection.height)
    })

    // Draw current selection
    if (currentSelection) {
      ctx.strokeRect(currentSelection.x, currentSelection.y, currentSelection.width, currentSelection.height)
    }
  }, [uploadedImage, selections, currentSelection])

  useEffect(() => {
    drawCanvas()
  }, [drawCanvas])

  const scaleSelectionsForImage = useCallback(
    (rects: Selection[]) => {
      const canvas = canvasRef.current
      const img = imageRef.current
      if (!canvas || !img || !naturalSize) return [] as Selection[]
      const sx = naturalSize.width / canvas.width
      const sy = naturalSize.height / canvas.height
      return rects.map((r) => ({
        x: Math.round(r.x * sx),
        y: Math.round(r.y * sy),
        width: Math.round(r.width * sx),
        height: Math.round(r.height * sy),
      }))
    },
    [naturalSize]
  )

  const handleCanvasMouseDown = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current) return

      const rect = canvasRef.current.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top

      if (selectedTool === "select") {
        setIsDrawing(true)
        setCurrentSelection({ x, y, width: 0, height: 0 })
      } else if (selectedTool === "deselect") {
        fetch(`${API_BASE}/deselect`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ selections, x: Math.round(x), y: Math.round(y) }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (Array.isArray(data.selections)) setSelections(data.selections)
          })
          .catch(() => {})
      }
    },
    [selectedTool],
  )

  const handleCanvasMouseMove = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isDrawing || !currentSelection || !canvasRef.current) return

      const rect = canvasRef.current.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top

      setCurrentSelection((prev) =>
        prev
          ? {
              ...prev,
              width: x - prev.x,
              height: y - prev.y,
            }
          : null,
      )
    },
    [isDrawing, currentSelection],
  )

  const handleCanvasMouseUp = useCallback(() => {
    if (
      isDrawing &&
      currentSelection &&
      Math.abs(currentSelection.width) > 10 &&
      Math.abs(currentSelection.height) > 10
    ) {
      const rect = {
        x: Math.min(currentSelection.x, currentSelection.x + currentSelection.width),
        y: Math.min(currentSelection.y, currentSelection.y + currentSelection.height),
        width: Math.abs(currentSelection.width),
        height: Math.abs(currentSelection.height),
      }
      fetch(`${API_BASE}/select`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selections, rect }),
      })
        .then((r) => r.json())
        .then((data) => {
          if (Array.isArray(data.selections)) setSelections(data.selections)
          else setSelections((prev) => [...prev, rect])
        })
        .catch(() => setSelections((prev) => [...prev, rect]))
    }
    setIsDrawing(false)
    setCurrentSelection(null)
  }, [isDrawing, currentSelection])

  const processImage = useCallback(async () => {
    if (!uploadedImage || selections.length === 0) return
    const endpoint = selectedTool === "crop" ? "crop" : selectedTool === "blackout" ? "blackout" : selectedTool === "blur" ? "blur" : "select_object"
    const base64 = uploadedImage.startsWith("data:") ? uploadedImage.split(",")[1] : uploadedImage
    const scaled = scaleSelectionsForImage(selections)
    try {
      const res = await fetch(`${API_BASE}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: base64, selections: scaled }),
      })
      const data = await res.json()
      if (data?.image_base64) setProcessedImage(`data:image/png;base64,${data.image_base64}`)
    } catch {}
  }, [uploadedImage, selections, selectedTool, scaleSelectionsForImage])

  const downloadImage = useCallback(() => {
    if (!processedImage) return

    const link = document.createElement("a")
    link.download = `anonymized-image-${Date.now()}.png`
    link.href = processedImage
    link.click()
  }, [processedImage])

  const resetTool = useCallback(() => {
    setSelections([])
    setProcessedImage(null)
    setCurrentSelection(null)
  }, [])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Tools Panel */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Square className="h-5 w-5" />
            Anonymization Tools
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {tools.map((tool) => {
            const Icon = tool.icon
            return (
              <Button
                key={tool.id}
                variant={selectedTool === tool.id ? "default" : "outline"}
                className={cn(
                  "w-full justify-start gap-2 h-auto p-3",
                  selectedTool === tool.id && "bg-primary text-primary-foreground",
                )}
                onClick={() => setSelectedTool(tool.id)}
              >
                <Icon className="h-4 w-4" />
                <div className="text-left">
                  <div className="font-medium">{tool.name}</div>
                  <div className="text-xs opacity-70">{tool.description}</div>
                </div>
              </Button>
            )
          })}

          <Separator />

          <div className="space-y-2">
            <Button onClick={processImage} disabled={!uploadedImage || selections.length === 0} className="w-full">
              Apply {selectedTool === "crop" ? "Crop" : selectedTool === "blackout" ? "Blackout" : selectedTool === "blur" ? "Blur" : "Select"}
            </Button>

            <Button
              onClick={resetTool}
              variant="outline"
              className="w-full bg-transparent"
              disabled={selections.length === 0}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset Selections
            </Button>
          </div>

          {selections.length > 0 && (
            <div className="pt-2">
              <Badge variant="secondary">
                {selections.length} selection{selections.length !== 1 ? "s" : ""}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Canvas Area */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Image Editor</CardTitle>
        </CardHeader>
        <CardContent>
          {!uploadedImage ? (
            <div className="border-2 border-dashed border-border rounded-lg p-12 text-center">
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">Upload an image</h3>
              <p className="text-muted-foreground mb-4">Select an image file to begin anonymization</p>
              <div className="space-y-2">
                <Label htmlFor="file-upload" className="sr-only">
                  Choose file
                </Label>
                <Input
                  id="file-upload"
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <Button onClick={() => fileInputRef.current?.click()}>Choose File</Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative border rounded-lg overflow-hidden bg-muted">
                <canvas
                  ref={canvasRef}
                  width={800}
                  height={600}
                  className="max-w-full h-auto cursor-crosshair"
                  onMouseDown={handleCanvasMouseDown}
                  onMouseMove={handleCanvasMouseMove}
                  onMouseUp={handleCanvasMouseUp}
                />
                <img
                  ref={imageRef}
                  src={uploadedImage || "/placeholder.svg"}
                  alt="Uploaded"
                  className="hidden"
                  onLoad={(e) => {
                    const target = e.currentTarget
                    setNaturalSize({ width: target.naturalWidth, height: target.naturalHeight })
                    drawCanvas()
                  }}
                />
              </div>

              {processedImage && (
                <div className="space-y-4">
                  <Separator />
                  <div>
                    <h3 className="text-lg font-medium mb-2">Processed Image</h3>
                    <div className="border rounded-lg overflow-hidden bg-muted mb-4">
                      <img src={processedImage || "/placeholder.svg"} alt="Processed" className="max-w-full h-auto" />
                    </div>
                    <Button onClick={downloadImage} className="w-full">
                      <Download className="h-4 w-4 mr-2" />
                      Download Anonymized Image
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
