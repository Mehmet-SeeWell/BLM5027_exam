# BLM5027 Midterms Project - Reinforcement Learning with Container Sorter
Bu projede, Q-Learning algoritmasını kullanarak farklı boyutlarda bir yığın konteyneri çıkış önceliklerini göz önünde bulundurarak sıralı bir şekilde iki adet limana istifleyebilecek bir ajan eğiteceğiz.

## Proje Detayları
Bu projede, bir kargo alanındaki konteynerleri alıp sırayla çıkarılacakları bir limana taşıyan bir düzenleyici (Sorter) tasarlanmıştır. Konteynerler, kargo alanından sırayla çıkarılmalıdır ve hepsinin sırasından bağımsız bir çıkış önceliği bulunmaktadır. 

Düzenleyicinin amacı, bu konteynerleri limanlara dizerken daha önce çıkarılması gereken konteynerleri daha yukarı ve daha sonra çıkarılması gereken konteynerleri daha aşağıya yerleştirmektir. Eğer ki önceliği olan bir konteyner altta kalırsa, onu çıkarmak için üstündeki konteynerleri hareket ettirmesi gerekmektedir ve bu da bulunan kısıtlı alandan ötürü çok büyük bir zaman kaybıdır. Var olan 2 limanın yanı sıra daha küçük bir geçici limanı bulunmaktadır ve konteynerlerin yerini değiştirirken yardımcı olsa da düzenlemenin sonunda bu limanda konteyner bulunmaması gerekmektedir.

Limanların boyutları, kargodaki bütün konteynerleri dizebilmeye yetecek kadar olmalıdır. Bu sebepten dolayı n adet konteyner için her bir limanda ⌈n/2⌉ adet boşluk vardır. Geçici limanda ise bunun yarısı olacak şekilde ⌊⌈n/2⌉/2⌋ boşluk bulunmaktadır.

Düzenleyi, her adımda 3 + 6 = 9 adet farklı eylemden birini gerçekleştirebilir:

- 0-2: Kargo alanından Limana konteyner yerleştirme (0: Birinci limana yerleştir, 1: İkinci limana yerleştir, 2: Geçici limana yerleştir)
- 3-8: Limanlar arası konteyner taşıma (3-4: Birinci limandan ikinci/geçici limana taşı, 5-6: İkinci limandan birinci/geçici limana taşı, 7-8: Geçici limandan birinci/ikinci limana taşı)

```
def place_to_port(port_id):
    if len(Sorter.cargo) > 0 and len(Sorter.ports[port_id]) < Sorter.port_capacity:
        container = Sorter.cargo.pop(0)
        Sorter.ports[port_id].append(container) ### Takes the first element of cargo and places it into the port
        return -1
    else:
        return -10 ### Illegal move

def place_to_temp_port():
    if len(Sorter.cargo) > 0 and len(Sorter.ports[2]) < Sorter.temp_port_capacity:
        container = Sorter.cargo.pop(0)
        Sorter.ports[2].append(container) ### Takes the first element of cargo and places it into the port
        return -1
    else:
        return -10 ### Illegal move

def move_from_port(source_id, target_id):
    if len(Sorter.ports[source_id]) > 0 and (
        (target_id == 2 and len(Sorter.ports[target_id]) < Sorter.temp_port_capacity) ### If moving to the temporary port
        or 
        (target_id < 2 and len(Sorter.ports[target_id]) < Sorter.port_capacity) ### If moving to the other two ports
        ): 
        
        container = Sorter.ports[source_id].pop(-1)
        Sorter.ports[target_id].append(container) ### Takes the last element of a port and moves it to another port

        return -1
    else:
        return -10 ### Illegal move
```

Limanlar arasında konteyner taşınırken sadece en üstte bulunan konteyner hareket ettirilebiliyor. Bu eylemlerin her biri zaman kaybına sebep olduğundan ötürü -1 ve imkansız oldukları durumlarda denenirlerse o zaman -10 puanlık bir cezaya sebep olurlar. Aynı zamanda her bir adımda düzenleyici, eylem gerçekleştirdikten sonra konteynerlerin düzeni üzerinden de değerlendirilir:

- Kargo alanında bulunan her bir konteyner başına -1 puan (Kargo alanını boşaltmayı ödüllendirmek adına)
- Eğer bütün limanlardaki konteynerler düzenli bir şekilde yerleştirilmiş ve geçici liman boş bırakıldıysa +1000 puan (Düzenleyicininn görevi tamamlanmıştır.)

```
def container_check():
    reward = 0
    
    ### Penalize keeping cargo in the queue (encourage placing)
    reward -= len(Sorter.cargo)
    
    ### If all the cargo are placed correctly
    if len(Sorter.cargo) == 0 and len(Sorter.ports[2]) == 0:
        if False not in [Sorter.is_sorted(n) for n in range(3)]:
            reward += 1000
    return reward
```

Modelin ilk versiyonlarında burada hem düzenli liman başına ödül ve geçici limanda bulunan konteyner başına ceza veriliyordu, fakat bu ikisi de modeli devamlı aynı konteyneri ileri geri hareket ettirmeye teşvik ettiğinden kaldırıldı.

## Model Yapısı
Bu model, önceki Taxi-v3 projesine göre çok daha fazla parçadan oluşmakta ve daha karmaşıktır. Bu sebepten ötürü de elimizdeki durum uzayı da çok daha büyük olacaktır ve bu hem her bir write/look-up eyleminin daha uzun süreceği hem de uygulama sırasında daha önce hiç karşılaşmadığımız bir duruma gelme riskinin var olduğu anlamına geliyor. En naif yaklaşım ile durum uzayımızı oluşturacak olursak o zaman n konteyner sayısı için:
Konteynerlerin sahip olabileceği konum sayısı = _m_ = n (Kargo) + ⌈n/2⌉ (Liman 1) + ⌈n/2⌉ (Liman 2) + ⌊⌈n/2⌉/2⌋ (Geçici Liman)
Toplam uzay boyutu: m^n

> 4 konteyner = 9^4 = 6,561  
> 5 konteyner = 12^5 = 248,832  
> 6 konteyner = 13^6 = 4,826,809  
> 7 konteyner = 17^7 = 410,338,673  
> 8 konteyner = 18^8 = 11,019,960,576  

Her durum için 9 farklı aksiyon bulunduğu için Q-tablosunun boyutu bu sayıların 9 katı şeklindedir.

Bu bize üstel büyüme gösteren bir uzay boyutu verdiğinden dolayı bütün hepsi için eğitmeye çalışmak ve bütün durumları hafızada tutmak mantıksızdır. Aynı zamanda da durum uzayının çok büyük bir kısmını yapılması imkansız durumlar kapsıyor (aynı konteynerın iki konumda bulunması gibi mesela) ve bunu düzelterek uzay boyutumuzu (m!/(m-n)!) boyutuna indirsek bile bu durum hesabını algoritmik bir şekilde yapmamızı zorlaştıracaktır ve aynı zamanda da tablolar hala çok büyük kalacaktır:

> 4 konteyner = 9!/(9-4)! = 3,024  
> 5 konteyner = 12!/(13-5)! = 95,040  
> 6 konteyner = 13!/(14-6)! = 1,235,520  
> 7 konteyner = 17!/(17-7)! = 98,017,920  
> 8 konteyner = 18!/(18-8)! = 1,764,322,560  

Bu sebepten ötürü bunun gibi bir projenin durum tablosunu çıkarabilmek için bazı durumları birlikte ele almalı ve durumları sadece ajan için önemli olacak ögelere indirgemeliyiz. Bu durum için aşağıdaki durumları enkode etmeye karar verdim:
- Kargoda sıradaki konteyner (n -> _n_)

- 1\. Limanın en üstündeki konteyner (n+1 -> _n\*(n+1)_)
- 1\. Limanın doluluğu (⌈n/2⌉ -> _n\*(n+1)\*⌈n/2⌉_)
- 1\. Limanın düzenli olup olmadığı (2 -> _2\*n\*(n+1)\*⌈n/2⌉_)

- 2\. Limanın en üstündeki konteyner (n+1 -> _2\*n\*((n+1)^2)\*⌈n/2⌉_)
- 2\. Limanın doluluğu (⌈n/2⌉ -> _2\*n\*((n+1)^2)\*(⌈n/2⌉^2)_)
- 2\. Limanın düzenli olup olmadığı (2 -> _4\*n\*((n+1)^2)\*(⌈n/2⌉^2)_)

- Geçici Limanın en üstündeki konteyner (n+1 -> _4\*n\*((n+1)^3)\*(⌈n/2⌉^2)_)
- Geçici Limanın doluluğu (⌊⌈n/2⌉/2⌋ -> _4\*n\*((n+1)^3)\*(⌈n/2⌉^2)\*⌊⌈n/2⌉/2⌋_)
- Geçici Limanın düzenli olup olmadığı (2 -> _8\*n\*((n+1)^3)\*(⌈n/2⌉^2)\*⌊⌈n/2⌉/2⌋_)

Bu hesapla durum uzay boyutlarımız, daha küçük değerler için büyüme gösterse de bir önceki gibi üstel artışa maruz kalmamaktadır.

> 4 konteyner = 8\*4\*(5^3)\*(2^2)*1 = 16,000  
> 5 konteyner = 8\*5\*(6^3)\*(3^2)*1 = 77,760  
> 6 konteyner = 8\*6\*(7^3)\*(3^2)*1 = 148,176  
> 7 konteyner = 8\*7\*(8^3)\*(4^2)*2 = 917,504  
> 8 konteyner = 8\*8\*(9^3)\*(4^2)*2 = 1,492,992  

Bunun üzerine boş olan limanları direkt tek durum olarak sayarsak ve "en üstteki konteyner" ve "düzenli olup olmadığı" faktörlerini hesaba katmazsak o zaman sayıları biraz daha azaltıp bu uzay boyutlarını elde ediyoruz:

> 4 konteyner = 13,005  
> 5 konteyner = 63,426  
> 6 konteyner = 124,579  
> 7 konteyner = 753,768
> 8 konteyner = 1,254,825  

```
def is_sorted(n): ### If a port is arranged correctly (lower priority above higher priority)
    for i in range(len(Sorter.ports[n]) - 1):
        if Sorter.ports[n][i] < Sorter.ports[n][i + 1]:
            return False
    return True

def port_state(n): ### The current state value of a port
    port = Sorter.ports[n]
    if len(port) == 0:
        return 0

    height = len(port)
    top_box = port[-1]
    sorted_flag = int(Sorter.is_sorted(n))

    return 1 + (
        (height - 1) * Sorter.number_of_containers * 2
        + top_box * 2
        + sorted_flag
    )

def get_current_state(): ### Find the current state of the system
    incoming = Sorter.cargo[0] if len(Sorter.cargo) > 0 else Sorter.number_of_containers

    main_port_states = 1 + Sorter.number_of_containers * Sorter.port_capacity * 2
    temp_port_states = 1 + Sorter.number_of_containers * Sorter.temp_port_capacity * 2

    port_1_state = Sorter.port_state(0)
    port_2_state = Sorter.port_state(1)
    temp_state = Sorter.port_state(2)

    state = incoming
    state = state * main_port_states + port_1_state
    state = state * main_port_states + port_2_state
    state = state * temp_port_states + temp_state

    return state
```

Q-Learning güncellemesi standart formülle yapılmaktadır:
Q(s, a) = (1 - _α_) \* Q(s, a) + _α_ \* (_r_ + _γ_ \* max(Q(s')))

s : Şu anki durum\
a : Şu anki eylem\
s': Bir sonraki durum

_α_ : learning rate (öğrenme oranı) [0.2]\
_γ_ : discount factor (indirim faktörü) [0.95]\
_r_ : reward (bu durumdaki alınan ödül)

```
def update_q_table(old_state, old_value, next_value, reward):
        Sorter.q_table[old_state, Sorter.action] = (1 - Sorter.learning_rate) * old_value + Sorter.learning_rate * (reward + Sorter.discount_factor * next_value)
```

Eylem seçimi için Epsilon Greedy algoritmasından yararlanacağız. Bu algoritmada verilen bir _ε_ değerine oranla model ya öğrendiği bilgiler arasından en optimal olanı yapar ya da rastgele eylemler gerçekleştirerek yeni bilgi edinmeye çalışır.

_ε_ : Epsilon [0.95 -> 0.01, Decay rate = 0.005%]

```
if rnd.uniform(0, 1) < Sorter.epsilon:
        Sorter.action = rnd.randrange(Sorter.num_of_actions)
else:
        Sorter.action = np.argmax(Sorter.q_table[old_state])
```


## Eğitim Süreci ve Sonuçlar
Eğitim süreci boyunca karşılaşılan en büyük problem, modelin aynı hamleyi hamle limitine ulaşana kadar tekrar tekrar yapmayı başka bir hamleyi denemekten daha uygun bulmasıydı. Buna engel olmak için yapılabilecek bazı çözümler olmasına rağmen (hamle hafızası bulundurup tekrar sayısına göre cezalandırmak gibi) bunların hepsi Epsilon-Greedy algoritması ile eğitim metodunun felsefesine ters kalacağından bu çözümleri uygulamaktan vazgeçildi. 

Bu sorun tamamen giderilemese de bazı ödül/ceza değerlerinin ayarlanması ile minimuma indirilmeye çabalanmıştır ve bunun yüzünden ödül/bölüm grafiğinde iyileşme görülse de bazı yerlerde belirgin ve büyük düşüşler gözlemlenebiliyor. Toplamda 60,000 episode'dan (bölümden) oluşan bir eğitim süreci sonucunda modelin 2,500'lik aralıklardaki ortalama ödül değeri -3200~ civarından +1000 civarına doğru hızlı bir iyileşme göstermiştir. Yapılan adımlar daha akıllıca ve daha tutarlı bir hale gelmeye başladıkça da her bir episode'un süresi üstel olarak daha kısa sürmeye başlamıştır.

<img width="635" height="463" alt="Screenshot (4745)" src="https://github.com/user-attachments/assets/2c297ffc-b032-4343-9b6a-0cc4926e7f2f" />

<img width="1188" height="577" alt="Screenshot (4744)" src="https://github.com/user-attachments/assets/f43ff2d5-aa37-4c19-9907-689428148ad6" />



<img width="795" height="475" alt="Screenshot (4750)" src="https://github.com/user-attachments/assets/d9bbd8e7-dd4e-4ffe-865c-25fcb1893ed2" />

<img width="1061" height="561" alt="Screenshot (4751)" src="https://github.com/user-attachments/assets/1f03d50e-1d43-468a-99b7-070ca017a5e5" />

<img width="800" height="500" alt="sortgif1" src="https://github.com/user-attachments/assets/10a84928-85b0-4cab-8070-e4154bb5698b" />

<img width="800" height="500" alt="sortgif2" src="https://github.com/user-attachments/assets/398c74f5-4ffb-4ba9-a92c-64710f83cf8e" />

<img width="800" height="500" alt="sortgif3" src="https://github.com/user-attachments/assets/947f027e-78e0-4794-bf17-e047158a30b5" />

<img width="800" height="500" alt="sortgif4" src="https://github.com/user-attachments/assets/ea55d9eb-53e8-4f48-852e-bc369d52a6ac" />

<img width="800" height="500" alt="sortgif5" src="https://github.com/user-attachments/assets/bb88b6ae-ce61-49b8-b7c9-d124a6d36304" />
