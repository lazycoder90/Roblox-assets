--[[
Jellyfish pet: follows the player, bobs and spins slowly.

Setup in Roblox Studio:
 1. Import jellyfish/export/JellyfishBody.fbx and JellyfishGlow.fbx with the 3D Importer.
 2. Upload jellyfish/jellyfish_texture.png as a Decal/Image, copy its asset id
    and paste it into TEXTURE_ID below (or set TextureID on both MeshParts by hand).
 3. Put a Model named "JellyfishPet" in ServerStorage containing the two MeshParts
    named "Body" and "Glow" (keep the position they have after import, they share one origin).
 4. Put this Script in ServerScriptService.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local TEXTURE_ID = "" -- e.g. "rbxassetid://123456789"
local FOLLOW_OFFSET = Vector3.new(3.5, 3, 3) -- right/up/behind the character
local BOB_HEIGHT, BOB_SPEED, SPIN_SPEED = 0.6, 2, 0.6
local PET_SCALE = 0.5 -- model is ~11 studs tall at 1.0

local template = ServerStorage:WaitForChild("JellyfishPet")

local function setupPet(character)
	local root = character:WaitForChild("HumanoidRootPart")
	local pet = template:Clone()
	pet.Name = "JellyfishPet_" .. character.Name
	pet:ScaleTo(PET_SCALE)

	local body, glow = pet:WaitForChild("Body"), pet:WaitForChild("Glow")
	for _, part in { body, glow } do
		part.Anchored = false
		part.CanCollide = false
		part.CanQuery = false
		part.Massless = true
		if TEXTURE_ID ~= "" then
			part.TextureID = TEXTURE_ID
		end
	end

	-- gold parts glow
	glow.Material = Enum.Material.Neon
	local light = Instance.new("PointLight")
	light.Color = Color3.fromRGB(255, 214, 90)
	light.Range = 14
	light.Brightness = 2
	light.Parent = glow

	local sparkles = Instance.new("ParticleEmitter")
	sparkles.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	sparkles.Color = ColorSequence.new(Color3.fromRGB(255, 230, 120))
	sparkles.Rate = 6
	sparkles.Lifetime = NumberRange.new(1, 2)
	sparkles.Speed = NumberRange.new(0.5, 1.5)
	sparkles.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) })
	sparkles.LightEmission = 1
	sparkles.Parent = glow

	-- weld glow to body so they move as one
	local weld = Instance.new("WeldConstraint")
	weld.Part0, weld.Part1 = body, glow
	weld.Parent = body

	pet.PrimaryPart = body
	pet.Parent = workspace
	body:SetNetworkOwner(nil)

	-- physical follow (smooth, no snapping)
	local attachment = Instance.new("Attachment")
	attachment.Parent = body
	local targetPart = Instance.new("Part")
	targetPart.Name = "PetTarget"
	targetPart.Anchored = true
	targetPart.CanCollide = false
	targetPart.CanQuery = false
	targetPart.Transparency = 1
	targetPart.Size = Vector3.one
	targetPart.Parent = pet
	local targetAtt = Instance.new("Attachment")
	targetAtt.Parent = targetPart

	local align = Instance.new("AlignPosition")
	align.Attachment0, align.Attachment1 = attachment, targetAtt
	align.MaxForce = math.huge
	align.Responsiveness = 12
	align.Parent = body
	local orient = Instance.new("AlignOrientation")
	orient.Attachment0, orient.Attachment1 = attachment, targetAtt
	orient.MaxTorque = math.huge
	orient.Responsiveness = 12
	orient.Parent = body

	local t0 = os.clock()
	local conn
	conn = RunService.Heartbeat:Connect(function()
		if not pet.Parent or not root.Parent then
			conn:Disconnect()
			pet:Destroy()
			return
		end
		local t = os.clock() - t0
		local bob = math.sin(t * BOB_SPEED) * BOB_HEIGHT
		local base = root.CFrame * CFrame.new(FOLLOW_OFFSET.X, FOLLOW_OFFSET.Y + bob, FOLLOW_OFFSET.Z)
		targetPart.CFrame = CFrame.new(base.Position) * CFrame.Angles(0, t * SPIN_SPEED, 0)
	end)
end

Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(setupPet)
	if player.Character then
		setupPet(player.Character)
	end
end)
for _, player in Players:GetPlayers() do
	player.CharacterAdded:Connect(setupPet)
	if player.Character then
		task.spawn(setupPet, player.Character)
	end
end
