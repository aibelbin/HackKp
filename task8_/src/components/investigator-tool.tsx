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

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)

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
        // Remove selection at this point
        setSelections((prev) =>
          prev.filter((sel) => !(x >= sel.x && x <= sel.x + sel.width && y >= sel.y && y <= sel.y + sel.height)),
        )
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
      setSelections((prev) => [
        ...prev,
        {
          x: Math.min(currentSelection.x, currentSelection.x + currentSelection.width),
          y: Math.min(currentSelection.y, currentSelection.y + currentSelection.height),
          width: Math.abs(currentSelection.width),
          height: Math.abs(currentSelection.height),
        },
      ])
    }
    setIsDrawing(false)
    setCurrentSelection(null)
  }, [isDrawing, currentSelection])

  const processImage = useCallback(async () => {
    if (!canvasRef.current || !uploadedImage || selections.length === 0) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    const img = imageRef.current

    if (!ctx || !img) return

    // Create a new canvas for processing
    const processCanvas = document.createElement("canvas")
    const processCtx = processCanvas.getContext("2d")

    if (!processCtx) return

    processCanvas.width = canvas.width
    processCanvas.height = canvas.height

    // Draw the original image
    processCtx.drawImage(img, 0, 0, canvas.width, canvas.height)

    // Apply effects to selected areas
    selections.forEach((selection) => {
      if (selectedTool === "blackout") {
        processCtx.fillStyle = "#000000"
        processCtx.fillRect(selection.x, selection.y, selection.width, selection.height)
      } else if (selectedTool === "blur") {
        // Simple blur effect using canvas filter
        const imageData = processCtx.getImageData(selection.x, selection.y, selection.width, selection.height)
        processCtx.filter = "blur(10px)"
        processCtx.putImageData(imageData, selection.x, selection.y)
        processCtx.filter = "none"
      } else if (selectedTool === "crop") {
        // For crop, we'll create a new canvas with just the selected area
        const cropCanvas = document.createElement("canvas")
        const cropCtx = cropCanvas.getContext("2d")
        if (cropCtx) {
          cropCanvas.width = selection.width
          cropCanvas.height = selection.height
          cropCtx.drawImage(
            processCanvas,
            selection.x,
            selection.y,
            selection.width,
            selection.height,
            0,
            0,
            selection.width,
            selection.height,
          )
          setProcessedImage(cropCanvas.toDataURL())
          return
        }
      }
    })

    setProcessedImage(processCanvas.toDataURL())
  }, [uploadedImage, selections, selectedTool])

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
              Apply {selectedTool === "crop" ? "Crop" : selectedTool === "blackout" ? "Blackout" : "Blur"}
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
                  onLoad={drawCanvas}
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
