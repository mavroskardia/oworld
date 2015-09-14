name = "Flashlight"
value = 100
types = EquipTypes.Not_Attack
jobs = JobTypes.All
locations = EquipLocation.Not_Equippable
desc = """A standard battery-powered flashlight that does, admittedly, kick
totally awesome ass."""

def onEquip(character, scene): scene.addScript("playerFlashlight")
def onStow(character, scene): scene.removeScript("playerFlashlight")
