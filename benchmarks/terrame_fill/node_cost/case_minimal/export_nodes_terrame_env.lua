-- Cost of every node of the TerraME GPM Network, before the cells are connected to it.
-- Same inputs and Network arguments as connectivity.lua of luccme-goldens (sources/fill); the GPM
-- fill is left out because only the node costs are wanted here.
--
--   cp export_nodes_terrame.lua <work dir>
--   docker run --rm -v <work dir>:/work profsergiocosta/terrame-luccme \
--       bash -c "cd /work && xvfb-run -a /opt/terrame/bin/terrame -autoclose export_nodes_terrame.lua"
--
-- Writes nodes_terrame.csv (x, y, cost, target, router) in the working directory.
-- Nodes are in network.netpoints and node.distance is the accumulated cost from the target, the value GPM
-- adds to the cell's off-network cost (gpm/lua/Network.lua). Run with TerraME 2.0.1 (sha256 846fa303...)
-- and the pinned gpm of terrame-docker 0.4.2: connectivity.lua then reproduces the golden to 5e-7 km, and
-- this script gives 119,331 nodes in about 8 s.
import("gis")
import("gpm")

local cs_file = tostring(filePath("br_cs_5880_25x25km.shp", "gpm"))
os.execute("cp " .. string.gsub(cs_file, "%.shp", ".*") .. " .")

local proj = Project{
    file = "connectivity_nodes.qgs",
    clean = true,
    title = "GTC nodes",
    cs = "br_cs_5880_25x25km.shp",
    roads = os.getenv("ROADS") or filePath("br_roads_5880.shp", "gpm"),
    ports = os.getenv("PORTS") or filePath("br_ports_5880.shp", "gpm")
}

local roads = CellularSpace{project = proj, layer = "roads", missing = 0}
local ports = CellularSpace{project = proj, layer = "ports"}

local network = Network{
    lines = roads,
    target = ports,
    progress = false,
    validate = false,
    inside = function(distance, line)
        return distance * 1e-3 * line.custo_ajus
    end,
    outside = function(distance)
        return distance * 1e-3 * 2
    end
}

local out = io.open(os.getenv("OUT") or "nodes_terrame.csv", "w")
out:write("x,y,cost,target,router\n")
local n = 0
forEachElement(network.netpoints, function(_, node)
    out:write(string.format("%.3f,%.3f,%.6f,%s,%s\n", node.point:getX(), node.point:getY(),
        node.distance, tostring(node.targetId), tostring(node.router == true)))
    n = n + 1
end)
out:close()
print(">>> nodes_terrame.csv: " .. n .. " nodes")
