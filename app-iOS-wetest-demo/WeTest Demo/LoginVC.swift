//
//  LoginVC.swift
//  WeTest Demo
//
//  Created by sergiotian on 2021/11/26.
//

import UIKit

class LoginVC: UIViewController, UITextFieldDelegate {
    @IBOutlet weak var tips: UILabel!
    @IBOutlet weak var email: UITextField!
    @IBOutlet weak var password: UITextField!
    
//    override func viewWillAppear(_ animated: Bool) {
//        self.navigationController.navigationBar.hidden = true;
//    }
    override func viewDidLoad() {
        super.viewDidLoad()
        email.delegate = self
        email.returnKeyType = UIReturnKeyType.done
        password.delegate = self
        password.returnKeyType = UIReturnKeyType.done

        // Do any additional setup after loading the view.
    }
    
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if segue.destination is PurchaseVC{
            let destination = segue.destination as! PurchaseVC
            print(email.text)
            destination.param = email.text!
            //destination.usermail.text = email.text!
            
        }
    }
    
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
        self.view?.endEditing(false)
        return true
    }

//
    
    override func shouldPerformSegue(withIdentifier identifier: String, sender: Any?) -> Bool {
        
        if identifier == "Success"{
            if email.hasText && password.hasText  {
                tips.text = "Log Out"
                print("Login Status:",String(tips.text ?? "none"))
                return true
            }else{
                tips.text = "Login Failed"
                return false
            }
        }
        return true
        
    }
    
    @IBAction func CrashTrigger(_ sender: UIButton) {
        preconditionFailure()
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
