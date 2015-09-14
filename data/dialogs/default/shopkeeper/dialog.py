def build_shopkeeper_dialog(scene, buyer, seller):
    class ItemDisplay(gui.BorderedControl):
        def __init__(self, item, depreciate=True, **kwargs):
            gui.BorderedControl.__init__(self, **kwargs)
            self.item = item
            self.depreciate = depreciate
            self._initComponents()
            
        def _initComponents(self):
            fc = (0,0,0)
            
            # Item Image
            image = gui.Image(parent=self, surface=self.item.image, width=50, height=50, borderWidth=2)        
            # Item Name
            name = gui.Label(parent=self, text=self.item.name, fontColor=fc)        
            # Item Count (if greater than 1)
            self.count = gui.Label(parent=self, text="Count: %d" % self.item.count if self.item.count > 0 else "", fontColor=fc)        
            # Item Cost
            value = self.item.worth if self.depreciate else self.item.fullValue
            cost = gui.Label(parent=self, text="Cost: %d" % value, fontColor=fc)
            
            # position the controls    
            image.x, image.y = 10, 10
    
            name.x = image.right + 5
            name.y = image.y+(image.height-name.height)/2
            
            self.count.x = image.x
            self.count.y = image.bottom + 5
            
            cost.x = self.count.x
            cost.y = self.count.bottom + 5
            
            self.add(image)
            self.add(name)
            self.add(self.count)
            self.add(cost)
        
    class ShopInterface(gui.Application):
        '''Constructs a shop interface based on a passed in actor's inventory.'''
        
        def __init__(self, scene, buyer, seller, **kwargs):
            gui.Application.__init__(self, **kwargs) 
            if 'backgroundColor' not in kwargs: self.backgroundColor = (0,0,0,50)
            
            self.scene = scene
            self.buyer = buyer
            self.seller = seller
            self.itemDisplayShown = None
            self.itemDisplayLabel = None
            self._initComponents()
            
        def __repr__(self): return 'ShopInterface'
        
        def _initComponents(self):
            # title
            title = gui.Label(text='Storekeeper Interface for %s' % self.seller.name, parent=self)
            title.x = 10
            title.y = 10
            self.add(title)
            
            # buyer/seller lists container
            self.frame = gui.BorderedControl(parent=self)
    
            # buyer's title
            buyerTitle = gui.Label(text="%s's Inventory" % self.buyer.name, parent=self.frame)
            buyerTitle.x = 10
            buyerTitle.y = 10
            
            # buyer's money
            self.buyerMoney = gui.Label(text='Money: %s' % self.buyer.money, parent=self.frame)
            self.buyerMoney.x = buyerTitle.x
            self.buyerMoney.y = buyerTitle.bottom + 10
            
            # build the buyer list
            self.buyerList = gui.ListBox(parent=self.frame, width=300, height=300)
    
            self.buyerList.x = self.buyerMoney.x
            self.buyerList.y = self.buyerMoney.bottom + 10
            
            # buy/sell buttons
            self.buyButton = gui.Button(text="Buy", width=50, height=50)
            self.buyButton.callback = self.buyButtonCb
            self.sellButton = gui.Button(text="Sell", width=50, height=50)
            self.sellButton.callback = self.sellButtonCb

            self.buyButton.x = self.buyerList.right + 10
            self.buyButton.y = self.buyerList.y + self.buyerList.height / 3

            self.sellButton.x = self.buyButton.x
            self.sellButton.y = self.buyButton.bottom + 10
            
            # seller's title       
            sellerTitle = gui.Label(text="%s's Inventory" % self.seller.name, parent=self.frame)
            sellerTitle.y = 10
            sellerTitle.x = self.buyButton.right + 10
            sellerTitle.y = buyerTitle.y            

            # seller's money
            self.sellerMoney = gui.Label(text="Money: %s" % self.seller.money, parent=self.frame)
            self.sellerMoney.x = sellerTitle.x
            self.sellerMoney.y = sellerTitle.bottom + 10
            
            # build the seller list
            self.sellerList = gui.ListBox(parent=self.frame, width=300, height=300)
                        
            self.sellerList.x = self.sellerMoney.x
            self.sellerList.y = self.sellerMoney.bottom + 10
            
            self.frame.add(buyerTitle)
            self.frame.add(self.buyerMoney)
            
            self.frame.add(self.buyerList)
            self.frame.add(self.buyButton)
            self.frame.add(self.sellButton)
            self.frame.add(sellerTitle)
            self.frame.add(self.sellerMoney)
            self.frame.add(self.sellerList)
            
            self.frame.width = max(self.frame.width, 10+self.buyerList.width+10+self.buyButton.width+10+self.sellerList.width+10)
            self.frame.height = max(self.frame.height, buyerTitle.height + self.buyerMoney.height + self.buyerList.height + 40)
            self.frame.x = (self.width-self.frame.width)/2
            self.frame.y = (self.height-self.frame.height)/2
    
            # done button
            doneButton = gui.Button(text="Done", callback=lambda x,y: y.ancestor.exit(), parent=self, width=100, height=50)
            doneButton.x = self.frame.right - doneButton.width
            doneButton.y = self.frame.bottom + 10
            
            self.add(doneButton)
            self.add(self.frame)
    
            self.populateList(self.buyerList, self.buyer, True)
            self.populateList(self.sellerList, self.seller, False)
            
        def populateList(self, list, actor, buyer):
            for item in actor.inventory.stowed:
                if item.count <= 0: continue
                id = ItemDisplay(item, buyer)
                id.borderRenderer = gui.RoundBorderRenderer(id, borderWidth=2, backgroundColor=(255,255,255))
                id.borderRenderer.cornerRadius = 20
                id.width = self.frame.width - 20
                id.y = 10            
                id.height = self.frame.y - 20
                id.x = (self.width-id.width)/2
                id.show = False
                self.add(id)
    
                lbl = gui.Label(text=item.name, width=list.width)
                ih = self.ItemHover(self, id, lbl, buyer)
                lbl.clicked = ih.clicked
                list.add(lbl)
                
        def redraw(self):
            self.buyerMoney.text = 'Money: %s' % self.buyer.money
            self.sellerMoney.text = 'Money: %s' % self.seller.money
            self.itemDisplayShown.show = False
            self.buyerList.removeAllChildren()
            self.populateList(self.buyerList, self.buyer, True)
            self.sellerList.removeAllChildren()
            self.populateList(self.sellerList, self.seller, False)
                
        def buyButtonCb(self, event, control):
            item = self.itemDisplayShown.item
            if self.buyer.canBuyItem(item):
                ynd = gui.Dialog.createYesNoDialog('Are you sure you want to buy the %s?' % item.name)
                ynd.run()
                if ynd.result: self.buyer.buyItem(self.seller, item)
            else:
                gui.Dialog.createOkDialog('You cannot afford to buy the %s.' % item.name).run()

            self.redraw()
            
        def sellButtonCb(self, event, control):
            item = self.itemDisplayShown.item
            if self.seller.canBuyItem(item, False):
                ynd = gui.Dialog.createYesNoDialog('Are you sure you want to sell the %s?' % item.name)
                ynd.run()
                if ynd.result: self.seller.buyItem(self.buyer, item, False)
            else:
                gui.Dialog.createOkDialog('%s cannot afford to buy the %s.' % (seller.name, item.name)).run()
            
            self.redraw()
                
        class ItemHover:        
            def __init__(self, app, itemDisplay, label, buyer=True): 
                self.app = app
                self.id = itemDisplay
                self.label = label
                self.buyer = buyer
                self.origBuyClicked = None
                self.origSellClicked = None
                
            def clicked(self, event, control):
                if self.app.itemDisplayShown:
                    self.app.itemDisplayShown.show = False
                if self.app.itemDisplayLabel:
                    self.app.itemDisplayLabel.backgroundColor = (0,0,0,0)
                
                self.id.show = True
                self.label.backgroundColor = (0,0,0,50)
                self.app.itemDisplayShown = self.id
                self.app.itemDisplayLabel = self.label
                
                if self.buyer: 
                    self.app.buyButton.enabled = False
                    self.app.sellButton.enabled = True
                else: 
                    self.app.buyButton.enabled = True
                    self.app.sellButton.enabled = False
                    
            def mouseEnter(self, event): self.id.show = True        
            def mouseLeave(self, event): self.id.show = False
    
    return ShopInterface(scene, buyer, seller)
    
def speak(otherFuncs, actor, scene):
    scene.playDialog(actor, 'I have a few items I can sell...')
    otherFuncs.build_shopkeeper_dialog(scene, scene.player, actor).run()