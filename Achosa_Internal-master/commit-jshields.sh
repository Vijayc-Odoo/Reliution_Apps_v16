cd ~/src/user
git status
echo "Continue?"
select yn in "Yes" "No"; do
    case $yn in
        Yes )
            echo $yn
            break
            ;;
        No ) exit;;
    esac
done
git config core.editor "vim"
git config user.email "shields.jp89@gmail.com"
git config user.name "jp-shields"
git commit --all
echo "Continue?"
select yn in "Yes" "No"; do
    case $yn in
        Yes )
            echo $yn
            break
            ;;
        No ) exit;;
    esac
done

git push https://jp-shields@github.com/restyn/achosa HEAD:AO-996

