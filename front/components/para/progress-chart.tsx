"use client"

import * as React from "react"
import { Bar, BarChart, XAxis, YAxis, Cell, CartesianGrid } from "recharts"
import { differenceInDays } from "date-fns"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import type { ParaProjectRead } from "@/lib/types/para"

interface ProgressChartProps {
  projects: ParaProjectRead[]
  progressById: Record<string, number>
  staleDays?: number
}

const ACTIVE_COLOR = "#4ECDC4"
const STALE_COLOR = "#f87171"

const chartConfig = {
  progress: { label: "Progress", color: ACTIVE_COLOR },
} satisfies ChartConfig

function isStale(project: ParaProjectRead, staleDays: number): boolean {
  if (!project.last_modified_at) return false
  return differenceInDays(new Date(), new Date(project.last_modified_at)) > staleDays
}

function truncateName(name: string, max = 14): string {
  return name.length > max ? `${name.slice(0, max)}…` : name
}

export function ProgressChart({
  projects,
  progressById,
  staleDays = 30,
}: ProgressChartProps) {
  if (projects.length === 0) return null

  const data = projects.map((p) => ({
    name: truncateName(p.name),
    fullName: p.name,
    progress: progressById[p.id] ?? 0,
    stale: isStale(p, staleDays),
  }))

  const chartHeight = Math.max(240, data.length * 40)

  return (
    <div className="border-[3px] border-black bg-[#fffdf5] p-4 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
      <h2 className="text-xl font-black uppercase tracking-tight mb-4">
        Project Progress
      </h2>
      <div className="overflow-y-auto max-h-[520px]">
        <ChartContainer
          config={chartConfig}
          className="w-full"
          style={{ height: chartHeight, aspectRatio: "unset" }}
        >
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 24, bottom: 0, left: 8 }}
            barCategoryGap="20%"
          >
            <CartesianGrid
              horizontal={false}
              strokeDasharray="3 3"
              stroke="#1a1a1a"
              strokeOpacity={0.15}
            />
            <XAxis
              type="number"
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              tick={{ fontSize: 12, fontWeight: 700, fill: "#1a1a1a" }}
              axisLine={{ stroke: "#1a1a1a", strokeWidth: 2 }}
              tickLine={{ stroke: "#1a1a1a" }}
            />
            <YAxis
              dataKey="name"
              type="category"
              width={120}
              tick={{ fontSize: 12, fontWeight: 700, fill: "#1a1a1a" }}
              axisLine={{ stroke: "#1a1a1a", strokeWidth: 2 }}
              tickLine={false}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  formatter={(value, _name, item) => (
                    <span className="font-bold">
                      {item.payload.fullName}: {value}%
                    </span>
                  )}
                  hideLabel
                />
              }
            />
            <Bar dataKey="progress" radius={0} maxBarSize={24}>
              {data.map((entry, index) => (
                <Cell
                  key={index}
                  fill={entry.stale ? STALE_COLOR : ACTIVE_COLOR}
                  stroke="#1a1a1a"
                  strokeWidth={2}
                />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </div>

      <div className="flex items-center gap-6 mt-4 text-sm font-bold">
        <div className="flex items-center gap-2">
          <div
            className="w-4 h-4 border-2 border-black"
            style={{ backgroundColor: ACTIVE_COLOR }}
          />
          <span>Active</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="w-4 h-4 border-2 border-black"
            style={{ backgroundColor: STALE_COLOR }}
          />
          <span>Abandoned (30d+)</span>
        </div>
      </div>
    </div>
  )
}
