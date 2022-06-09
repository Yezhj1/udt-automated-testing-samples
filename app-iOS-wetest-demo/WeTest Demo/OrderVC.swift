//
//  OrderVC.swift
//  WeTest Demo
//
//  Created by sergiotian on 2021/11/26.
//

import UIKit

class OrderVC: UIViewController {

    @IBOutlet weak var orderDetail: UITextView!
    @IBOutlet weak var orderCount: UILabel!
    var itemList:[EachItem] = []
    override func viewDidLoad() {
        super.viewDidLoad()
        var stringRepresentation:String = "Hi, Here is your Shopping Cart:  "
        for eachitem in itemList{
            stringRepresentation.append(eachitem.title+",")
        }
        
        orderDetail.text = stringRepresentation
        orderCount.text = "Total:\(itemList.count)"

        // Do any additional setup after loading the view.
    }
    
    

    /*
    // MARK: - Navigation

    // In a storyboard-based application, you will often want to do a little preparation before navigation
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        // Get the new view controller using segue.destination.
        // Pass the selected object to the new view controller.
    }
    */

}
