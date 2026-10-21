-- Builds an .aseprite file from a manifest written by pxo_to_aseprite.py.
-- Run by Aseprite in batch mode:
--   Aseprite.exe -b --script-param manifest=<path> --script aseprite_build.lua
--
-- The manifest is a plain text file, one record per line, tab separated:
--   size <w> <h>
--   out <path to write>
--   layer <name> <visible 0/1> <opacity 0-255>        (bottom to top)
--   frame <duration in seconds>
--   cel <layer index 1-based> <frame index 1-based> <png path>
--   tag <name> <from frame> <to frame>

local manifest = app.params["manifest"]
if not manifest then
  print("no manifest given")
  return
end

local function split(line)
  local out = {}
  for field in (line .. "\t"):gmatch("([^\t]*)\t") do
    table.insert(out, field)
  end
  return out
end

local size, out_path = nil, nil
local layers, frames, cels, tags = {}, {}, {}, {}
for line in io.lines(manifest) do
  local f = split(line)
  if f[1] == "size" then
    size = { tonumber(f[2]), tonumber(f[3]) }
  elseif f[1] == "out" then
    out_path = f[2]
  elseif f[1] == "layer" then
    table.insert(layers, { name = f[2], visible = f[3] == "1", opacity = tonumber(f[4]) })
  elseif f[1] == "frame" then
    table.insert(frames, tonumber(f[2]))
  elseif f[1] == "cel" then
    table.insert(cels, { layer = tonumber(f[2]), frame = tonumber(f[3]), path = f[4] })
  elseif f[1] == "tag" then
    table.insert(tags, { name = f[2], from = tonumber(f[3]), to = tonumber(f[4]) })
  end
end

local sprite = Sprite(size[1], size[2], ColorMode.RGB)
-- A new sprite starts with one layer and one frame.
local made = { sprite.layers[1] }
for i = 2, #layers do
  table.insert(made, sprite:newLayer())
end
for i, spec in ipairs(layers) do
  made[i].name = spec.name
  made[i].isVisible = spec.visible
  made[i].opacity = spec.opacity
end
for i = 2, #frames do
  sprite:newEmptyFrame()
end
for i, seconds in ipairs(frames) do
  sprite.frames[i].duration = seconds
end
for _, cel in ipairs(cels) do
  local image = Image { fromFile = cel.path }
  sprite:newCel(made[cel.layer], sprite.frames[cel.frame], image, Point(0, 0))
end
for _, tag in ipairs(tags) do
  local t = sprite:newTag(tag.from, tag.to)
  t.name = tag.name
end
sprite:saveAs(out_path)
sprite:close()
print("wrote " .. out_path)
