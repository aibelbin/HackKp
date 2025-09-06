import { InvestigatorTool } from "@/components/investigator-tool"

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto py-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-foreground mb-2">Investigator Web Tool</h1>
          <p className="text-muted-foreground">Professional image anonymization and tip generation tool</p>
        </div>
        <InvestigatorTool />
      </div>
    </main>
  )
}
