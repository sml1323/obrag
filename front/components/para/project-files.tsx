import * as React from "react"
import { formatDistanceToNow } from "date-fns"
import { ParaFileRead } from "@/lib/types/para"
import { cn } from "@/lib/utils"

interface ProjectFilesProps {
  files: ParaFileRead[];
  isOpen: boolean;
}

export function ProjectFiles({ files, isOpen }: ProjectFilesProps) {
  return (
    <div 
      className={cn(
        "transition-all duration-300 ease-in-out overflow-hidden bg-white",
        isOpen ? "max-h-[300px] border-t-2 border-black" : "max-h-0 border-none"
      )}
    >
      <div className="overflow-y-auto max-h-[300px]">
        {files.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500 italic">
            No files in this project
          </div>
        ) : (
          <table className="w-full text-left text-sm border-collapse">
            <thead className="bg-[#f0f0f0] sticky top-0 z-10 font-bold border-b-2 border-black">
              <tr>
                <th className="p-2 border-r-2 border-black w-1/2">File Name</th>
                <th className="p-2 w-1/2">Modified</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file, index) => (
                <tr 
                  key={file.id} 
                  className={cn(
                    "border-b border-black last:border-0",
                    index % 2 === 0 ? "bg-[#fffdf5]" : "bg-white" // Cream and white stripes
                  )}
                >
                  <td className="p-2 border-r-2 border-black truncate max-w-[150px]" title={file.relative_path}>
                    {file.name}
                  </td>
                  <td className="p-2 text-gray-600 text-xs">
                    {formatDistanceToNow(new Date(file.last_modified_at), { addSuffix: true })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
