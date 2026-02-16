"use client";

import { useEffect, useState, useMemo, ComponentType } from "react";
import dynamic from "next/dynamic";
import { listCollections, getCollectionVectors } from "@/lib/api/embedding";
import type {
  CollectionInfo,
  VectorPoint,
  VectorVisualizationResponse,
} from "@/lib/types/embedding";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import type { PlotParams } from "react-plotly.js";

const Plot = dynamic(
  () => import("react-plotly.js").then((mod) => mod.default),
  { ssr: false }
) as ComponentType<PlotParams>;

const CATEGORY_COLORS: Record<string, string> = {
  "0.Resource": "#FF6B35",
  "1.Zettelkasten": "#4ECDC4",
  "2.Area": "#FFE66D",
  "3.Planner": "#95E1D3",
  "4.Archive": "#F38181",
  unknown: "#A0AEC0",
};

function getCategoryColor(category: string, index: number): string {
  if (CATEGORY_COLORS[category]) {
    return CATEGORY_COLORS[category];
  }
  const fallbackColors = [
    "#FF6B35",
    "#4ECDC4",
    "#FFE66D",
    "#95E1D3",
    "#F38181",
    "#AA96DA",
    "#FCBAD3",
    "#A8D8EA",
  ];
  return fallbackColors[index % fallbackColors.length];
}

function getSelectedPaths(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const stored = localStorage.getItem("embedding-scope");
    if (stored) {
      const parsed = JSON.parse(stored);
      return new Set(Array.isArray(parsed) ? parsed : []);
    }
  } catch {
    // ignore parse errors
  }
  return new Set();
}

function isPathIncluded(relativePath: string, selectedPaths: Set<string>): boolean {
  if (selectedPaths.size === 0) return true;
  
  for (const selectedPath of selectedPaths) {
    if (relativePath === selectedPath || relativePath.startsWith(selectedPath + "/")) {
      return true;
    }
  }
  return false;
}

function extractCategory(relativePath: string): string {
  if (!relativePath) return "unknown";
  
  const parts = relativePath.split("/");
  
  if (parts.length >= 2) {
    return parts[parts.length - 2];
  }
  
  return parts[0] || "unknown";
}

type DimensionMode = "2d" | "3d";

export function EmbeddingVisualization() {
  const [collections, setCollections] = useState<CollectionInfo[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>("");
  const [vectorData, setVectorData] = useState<VectorVisualizationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dimensionMode, setDimensionMode] = useState<DimensionMode>("3d");

  useEffect(() => {
    async function fetchCollections() {
      try {
        const response = await listCollections();
        setCollections(response.collections);
        if (response.collections.length > 0 && !selectedCollection) {
          setSelectedCollection(response.collections[0].name);
        }
      } catch (err) {
        console.error("Failed to fetch collections:", err);
      }
    }
    fetchCollections();
  }, []);

  const handleVisualize = async () => {
    if (!selectedCollection) return;

    setIsLoading(true);
    setError(null);

    try {
      const dimensions = dimensionMode === "3d" ? 3 : 2;
      const data = await getCollectionVectors(selectedCollection, 500, 30, dimensions);
      setVectorData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch vectors");
    } finally {
      setIsLoading(false);
    }
  };

  const plotData = useMemo(() => {
    if (!vectorData || vectorData.points.length === 0) return null;

    const selectedPaths = getSelectedPaths();
    const filteredPoints = vectorData.points.filter((point) =>
      isPathIncluded(point.source || "", selectedPaths)
    );

    if (filteredPoints.length === 0) return null;

    const categoryMap = new Map<string, VectorPoint[]>();
    filteredPoints.forEach((point) => {
      const category = extractCategory(point.source || "");
      if (!categoryMap.has(category)) {
        categoryMap.set(category, []);
      }
      categoryMap.get(category)!.push(point);
    });

    const traces: Plotly.Data[] = [];
    let colorIndex = 0;
    const is3D = vectorData.dimensions === 3;

    categoryMap.forEach((points, category) => {
      if (is3D) {
        traces.push({
          type: "scatter3d",
          mode: "markers",
          name: category,
          x: points.map((p) => p.x),
          y: points.map((p) => p.y),
          z: points.map((p) => p.z),
          text: points.map(
            (p) => `${category}<br>${p.text.substring(0, 100)}...`
          ),
          hoverinfo: "text",
          marker: {
            size: 5,
            color: getCategoryColor(category, colorIndex),
            opacity: 0.8,
          },
        });
      } else {
        traces.push({
          type: "scatter",
          mode: "markers",
          name: category,
          x: points.map((p) => p.x),
          y: points.map((p) => p.y),
          text: points.map(
            (p) => `${category}<br>${p.text.substring(0, 100)}...`
          ),
          hoverinfo: "text",
          marker: {
            size: 8,
            color: getCategoryColor(category, colorIndex),
            opacity: 0.8,
          },
        });
      }
      colorIndex++;
    });

    return traces;
  }, [vectorData]);

  const selectedInfo = collections.find((c) => c.name === selectedCollection);
  const is3D = vectorData?.dimensions === 3;
  
  const filteredPointCount = useMemo(() => {
    if (!vectorData) return 0;
    const selectedPaths = getSelectedPaths();
    return vectorData.points.filter((p) => isPathIncluded(p.source || "", selectedPaths)).length;
  }, [vectorData]);

  const displayedCategories = useMemo(() => {
    if (!vectorData) return [];
    const selectedPaths = getSelectedPaths();
    const filteredPoints = vectorData.points.filter((p) => 
      isPathIncluded(p.source || "", selectedPaths)
    );
    const categories = new Set(filteredPoints.map((p) => extractCategory(p.source || "")));
    return Array.from(categories).sort();
  }, [vectorData]);

  return (
    <div className="border-4 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-black uppercase">Vector Visualization</h2>
        <div className="flex gap-2">
          {selectedInfo && (
            <div className="bg-gray-200 border-2 border-black px-3 py-1 font-bold">
              {selectedInfo.count} Total
            </div>
          )}
          {vectorData && (
            <div className="bg-[#4ECDC4] border-2 border-black px-3 py-1 font-bold">
              {filteredPointCount} Filtered
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-4 mb-6 flex-wrap">
        <Select value={selectedCollection} onValueChange={setSelectedCollection}>
          <SelectTrigger className="w-[300px] border-2 border-black">
            <SelectValue placeholder="Select collection" />
          </SelectTrigger>
          <SelectContent>
            {collections.map((col) => (
              <SelectItem key={col.name} value={col.name}>
                {col.model_name || col.name} ({col.count})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex border-2 border-black">
          <button
            onClick={() => setDimensionMode("2d")}
            className={`px-4 py-2 font-bold transition-colors ${
              dimensionMode === "2d"
                ? "bg-[#FFE66D] text-black"
                : "bg-white text-gray-600 hover:bg-gray-100"
            }`}
          >
            2D
          </button>
          <button
            onClick={() => setDimensionMode("3d")}
            className={`px-4 py-2 font-bold border-l-2 border-black transition-colors ${
              dimensionMode === "3d"
                ? "bg-[#FFE66D] text-black"
                : "bg-white text-gray-600 hover:bg-gray-100"
            }`}
          >
            3D
          </button>
        </div>

        <Button
          onClick={handleVisualize}
          disabled={!selectedCollection || isLoading}
          className="border-3 border-black font-bold px-6 bg-[#FF6B35] hover:bg-[#FF8C60] hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing t-SNE...
            </>
          ) : (
            "VISUALIZE"
          )}
        </Button>
      </div>

      {error && (
        <div className="border-2 border-red-500 bg-red-50 text-red-700 p-4 mb-4">
          {error}
        </div>
      )}

      {plotData && is3D && (
        <div className="border-2 border-black bg-gray-50">
          <Plot
            data={plotData}
            layout={{
              title: { text: `3D Embedding Space: ${selectedCollection}` },
              scene: {
                xaxis: { title: { text: "x" }, showgrid: true, gridcolor: "#ddd" },
                yaxis: { title: { text: "y" }, showgrid: true, gridcolor: "#ddd" },
                zaxis: { title: { text: "z" }, showgrid: true, gridcolor: "#ddd" },
                bgcolor: "#fafafa",
              },
              width: 900,
              height: 600,
              margin: { r: 10, b: 10, l: 10, t: 50 },
              paper_bgcolor: "#fafafa",
              showlegend: true,
              legend: {
                x: 1,
                y: 0.9,
                bgcolor: "rgba(255,255,255,0.9)",
                bordercolor: "#000",
                borderwidth: 1,
              },
            }}
            config={{
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ["lasso2d", "select2d"],
            }}
          />
        </div>
      )}

      {plotData && !is3D && (
        <div className="border-2 border-black bg-gray-50">
          <Plot
            data={plotData}
            layout={{
              title: { text: `2D Embedding Space: ${selectedCollection}` },
              xaxis: { title: { text: "x" }, showgrid: true, gridcolor: "#ddd" },
              yaxis: { title: { text: "y" }, showgrid: true, gridcolor: "#ddd" },
              width: 900,
              height: 600,
              margin: { r: 50, b: 50, l: 50, t: 50 },
              paper_bgcolor: "#fafafa",
              plot_bgcolor: "#fafafa",
              showlegend: true,
              legend: {
                x: 1,
                y: 0.9,
                bgcolor: "rgba(255,255,255,0.9)",
                bordercolor: "#000",
                borderwidth: 1,
              },
            }}
            config={{
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ["lasso2d", "select2d"],
            }}
          />
        </div>
      )}

      {!plotData && !isLoading && !error && (
        <div className="border-2 border-dashed border-gray-300 h-[400px] flex items-center justify-center">
          <p className="text-gray-500 text-lg">
            Select a collection and click VISUALIZE to see embedding space
          </p>
        </div>
      )}

      {displayedCategories.length > 0 && (
        <div className="mt-4 flex gap-2 flex-wrap">
          {displayedCategories.map((cat, i) => (
            <div
              key={cat}
              className="flex items-center gap-2 px-3 py-1 border-2 border-black"
              style={{ backgroundColor: getCategoryColor(cat, i) }}
            >
              <span className="font-bold text-sm">{cat}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
