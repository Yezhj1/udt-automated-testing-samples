//
//  ItemCellVC.swift
//  WeTest Demo
//
//  Created by sergiotian on 2021/11/26.
//

import UIKit

class ItemCellVC: UITableViewCell {

    @IBOutlet weak var markSelectImg: UIImageView!
    @IBOutlet weak var itemName: UILabel!
    override func awakeFromNib() {
        super.awakeFromNib()
        // Initialization code
    }

    override func setSelected(_ selected: Bool, animated: Bool) {
        super.setSelected(selected, animated: animated)

        // Configure the view for the selected state
    }

}


struct EachItem {
    var title:String
    var isSelect:Bool
}
