//
//  PurchaseVC.swift
//  WeTest Demo
//
//  Created by sergiotian on 2021/11/26.
//

import UIKit

class PurchaseVC: UIViewController {
    
    

    
    @IBOutlet weak var itemTableView: UITableView!
    @IBOutlet weak var usermail: UILabel!
    var param:String = ""
    
    
    //let items = ["Item1","Item2","Item3","Item4","Item5","Item6","Item7","Item8","Item9","Item10","Item11","Item12"]
    var itemList = [EachItem(title: "Item1", isSelect: false),EachItem(title: "Item2", isSelect: false),EachItem(title: "Item3", isSelect: false),EachItem(title: "Item4", isSelect: false),EachItem(title: "Item5", isSelect: false),EachItem(title: "Item6", isSelect: false),EachItem(title: "Item7", isSelect: false),EachItem(title: "Item8", isSelect: false),EachItem(title: "Item9", isSelect: false),EachItem(title: "Item10", isSelect: false),]
    
    var selectItem:[EachItem] = []
   
    
    override func viewDidLoad() {
        super.viewDidLoad()
        usermail.text = param
        selectItem = []
        print("param:\(param)")
        
        itemTableView.delegate = self
        itemTableView.dataSource = self
        
        
    }
    @IBAction func clickSubmit(_ sender: UIButton) {
        print("Hello\(itemList.count)")
        selectItem = []
        for (idx,item) in itemList.enumerated() {
            if item.isSelect == true {
                print("index: \(idx), name: \(item.title)")
                selectItem.append(item)
            }
        }
    }
    
    
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if segue.destination is OrderVC{
            let destination = segue.destination as! OrderVC
//            for eachItem in itemList{
//                if eachItem.isSelect == true {
//                    selectItem.append(eachItem)
//                }
//            }
            destination.itemList = selectItem
            
        }
    }
    

//
    
    override func shouldPerformSegue(withIdentifier identifier: String, sender: Any?) -> Bool {
        
        if identifier == "OrderSuccess"{
            print("Already Selected:\(selectItem.count)")
            if selectItem.count == 0  {
                print("No Item Selected")
                showMsgbox(_message: "No Item Selected")
//                print("Login Status:",String(tips.text ?? "none"))
                return false
            }
        }
        return true
        
    }
    
    
    func showMsgbox(_message: String, _title: String = "Error"){
            
        let alert = UIAlertController(title: _title, message: _message, preferredStyle: UIAlertController.Style.alert)
            let btnOK = UIAlertAction(title: "Ok", style: .default, handler: nil)
            alert.addAction(btnOK)
            self.present(alert, animated: true, completion: nil)
    }
    
}

extension PurchaseVC: UITableViewDelegate,UITableViewDataSource{
    func numberOfSections(in tableView: UITableView) -> Int {
        return 1
    }
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return itemList.count
    }
    
    
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = itemTableView.dequeueReusableCell(withIdentifier: "ItemCell", for: indexPath) as! ItemCellVC
        let item = itemList[indexPath.row]
        
        cell.itemName.text = item.title
        
        cell.markSelectImg.image = item.isSelect == true ? UIImage(named: "wetest") : UIImage(named:"pencil.slash")
        
        return cell
    }
    
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        guard let cell = tableView.cellForRow(at: indexPath) as? ItemCellVC else {return}
        
        var item = itemList[indexPath.row]
        item.isSelect = !item.isSelect
        
        itemList.remove(at: indexPath.row)
        itemList.insert(item, at: indexPath.row)
        cell.markSelectImg.image = item.isSelect == true ? UIImage(named: "wetest") : UIImage(named:"pencil.slash")
    }
}
