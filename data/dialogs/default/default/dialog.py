def speak(actor, scene):
    
    if "already_spoke" in actor.state and actor.state["already_spoke"]:
        result = scene.playDialogWithYesNo(actor, "Do you want something else?")
        if result:
            scene.playDialog(actor, "Well, I don't really have anything right now, but maybe later?", backgroundColor=(100,100,0,250))
        else:
            scene.playDialog(actor, "Fine with me, good luck.", backgroundColor=(100,100,0,250))
    else:
        scene.playDialog(actor, """Welcome to Overworld, %s. I am %s and just wanted you to \
        know that this dialog is coming from a script.""" % (scene.player.name, actor.name))
        actor.state["already_spoke"] = True
    